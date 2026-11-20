"""Alarm sound manager using Android ToneGenerator."""

import logging
import threading

from java import jclass

logger = logging.getLogger("HostelAlarm.alarm")

ToneGenerator = jclass("android.media.ToneGenerator")
AudioManager = jclass("android.media.AudioManager")


class AlarmManager:
    """Manages alarm sound state and playback."""

    def __init__(self):
        self._tone = None
        self._siren_timer = None
        self._active = False
        logger.debug("AlarmManager initialized")

    def check(self, stars, threshold):
        """Check if alarm should trigger and manage sound."""
        should_alarm = stars <= threshold
        logger.debug("check: stars=%d, threshold=%d, should_alarm=%s", stars, threshold)

        if should_alarm and not self._active:
            logger.warning("ALARM TRIGGERED: stars=%d <= threshold=%d", stars, threshold)
            self.start()
        elif not should_alarm and self._active:
            logger.info("ALARM cleared: stars=%d > threshold=%d", stars, threshold)
            self.stop()

    def start(self):
        """Start alarm siren."""
        if self._active:
            logger.debug("Alarm already active, skipping")
            return
        logger.info("Starting alarm siren")
        try:
            if self._tone is None:
                self._tone = ToneGenerator(AudioManager.STREAM_ALARM, 100)
                logger.debug("ToneGenerator created")
            self._active = True
            self._play_siren_cycle(0)
        except Exception as e:
            logger.exception("Failed to start alarm")
            self._active = False

    def _play_siren_cycle(self, count):
        """Play one siren tone cycle, alternating between two tones."""
        if not self._active or self._tone is None:
            logger.debug("Siren stopped: active=%s, tone=%s", self._active, self._tone)
            return
        if count >= 19:  # 19 * 1.5s = 28.5s ≈ 29s
            logger.info("Siren complete: 19 cycles")
            self.stop()
            return

        tone_type = (
            ToneGenerator.TONE_PROP_BEEP
            if count % 2 == 0
            else ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD
        )
        logger.debug("Siren cycle %d: tone=%s, duration=1500ms", count, tone_type)
        try:
            self._tone.startTone(tone_type, 1500)
        except Exception as e:
            logger.exception("startTone failed for cycle %d", count)
            self.stop()
            return

        self._siren_timer = threading.Timer(1.5, self._play_siren_cycle, [count + 1])
        self._siren_timer.daemon = True
        self._siren_timer.start()

    def stop(self):
        """Stop alarm sound."""
        if not self._active:
            return
        logger.info("Stopping alarm siren")
        try:
            if self._siren_timer is not None:
                self._siren_timer.cancel()
                self._siren_timer = None
            if self._tone is not None:
                self._tone.stopTone()
                self._tone.release()
                self._tone = None
                logger.debug("ToneGenerator released")
        except Exception as e:
            logger.exception("Error stopping alarm")
        finally:
            self._active = False

    def is_active(self):
        """Check if alarm is currently active."""
        return self._active
