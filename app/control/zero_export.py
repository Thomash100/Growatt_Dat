from __future__ import annotations

from datetime import datetime

from app.control import safety
from app.models import ControlDecision, ControlSettings, Measurement, utc_now


class ZeroExportController:
    def decide(
        self,
        measurement: Measurement | None,
        settings: ControlSettings,
        *,
        now: datetime | None = None,
    ) -> ControlDecision:
        current_time = now or utc_now()
        current_output = self._current_output(measurement, settings)

        if not settings.zero_export_enabled:
            return self._decision(
                current_time,
                measurement,
                settings,
                current_output,
                current_output,
                "manual",
                "zero_export_disabled",
            )

        valid = safety.validate_measurement(measurement)
        if not valid.ok:
            return self._decision(
                current_time,
                measurement,
                settings,
                current_output,
                safety.clamp_output_power(current_output, settings),
                "zero_export",
                valid.reason,
                valid.reason,
            )

        assert measurement is not None

        fresh = safety.measurement_is_fresh(
            measurement,
            settings.stale_measurement_seconds,
            now=current_time,
        )
        if not fresh.ok:
            target = current_output - settings.output_step_w
            return self._decision(
                current_time,
                measurement,
                settings,
                current_output,
                self._apply_change(current_output, target, settings),
                "zero_export",
                fresh.reason,
                fresh.reason,
            )

        soc = safety.soc_is_safe(measurement, settings.min_soc_percent)
        if not soc.ok:
            target = current_output - settings.output_step_w
            return self._decision(
                current_time,
                measurement,
                settings,
                current_output,
                self._apply_change(current_output, target, settings),
                "zero_export",
                soc.reason,
                soc.reason,
            )

        proposed_target = current_output
        reason = "within_deadband"
        increase_threshold_w = settings.grid_power_band_min_w + settings.grid_power_band_max_w

        if measurement.grid_power_w < -settings.grid_power_band_min_w:
            proposed_target = current_output - settings.output_step_w
            reason = "reduce_export"
        elif measurement.grid_power_w > increase_threshold_w:
            proposed_target = current_output + settings.output_step_w
            reason = "increase_due_to_import"
        elif settings.grid_power_band_min_w <= measurement.grid_power_w <= settings.grid_power_band_max_w:
            proposed_target = current_output
            reason = "within_deadband"
        else:
            proposed_target = current_output
            reason = "within_deadband"

        proposed_target = self._apply_change(current_output, proposed_target, settings)

        if proposed_target > current_output:
            increase = safety.can_increase_output(measurement, settings, now=current_time)
            if not increase.ok:
                return self._decision(
                    current_time,
                    measurement,
                    settings,
                    current_output,
                    current_output,
                    "zero_export",
                    increase.reason,
                    increase.reason,
                )

        return self._decision(
            current_time,
            measurement,
            settings,
            current_output,
            proposed_target,
            "zero_export",
            reason,
        )

    @staticmethod
    def _current_output(measurement: Measurement | None, settings: ControlSettings) -> int:
        if measurement is None:
            return settings.min_output_power_w
        return safety.clamp_output_power(measurement.output_power_w, settings)

    @staticmethod
    def _apply_change(current_output: int, proposed_target: int, settings: ControlSettings) -> int:
        clamped = safety.clamp_output_power(proposed_target, settings)
        if clamped != proposed_target and clamped != current_output:
            return clamped
        if abs(clamped - current_output) < settings.min_output_change_w:
            return safety.clamp_output_power(current_output, settings)
        return clamped

    @staticmethod
    def _decision(
        timestamp: datetime,
        measurement: Measurement | None,
        settings: ControlSettings,
        current_output: int,
        target_output: int,
        control_mode: str,
        reason: str,
        error_status: str | None = None,
    ) -> ControlDecision:
        return ControlDecision(
            timestamp=timestamp,
            current_output_power_w=safety.clamp_output_power(current_output, settings),
            target_output_power_w=safety.clamp_output_power(target_output, settings),
            grid_power_w=None if measurement is None else measurement.grid_power_w,
            battery_soc=None if measurement is None else measurement.battery_soc,
            zero_export_enabled=settings.zero_export_enabled,
            control_mode=control_mode,
            reason=reason,
            error_status=error_status,
        )
