import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import Config

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self) -> None:
        try:
            configure_credentials(
                yandex_credentials=creds.YandexCredentials(
                    api_key=Config.YANDEX_SPEECHKIT_API_KEY
                )
            )
            logger.info("Yandex SpeechKit credentials configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure SpeechKit credentials: {e}", exc_info=True)
            raise

    def _create_recognition_model(self):
        model = model_repository.recognition_model()
        model.model = Config.SPEECHKIT_MODEL
        model.language = Config.SPEECHKIT_LANGUAGE
        model.audio_processing_type = AudioProcessingType.Full
        return model

    def _save_bytesio_to_temp(self, data: BytesIO, suffix: str) -> Path:
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp_file:
            data.seek(0)
            tmp_file.write(data.read())
            return Path(tmp_file.name)

    def _extract_text_from_result(self, result) -> str:
        transcribed_text = ""
        for channel_result in result:
            if channel_result.normalized_text:
                transcribed_text += channel_result.normalized_text
            elif channel_result.raw_text:
                transcribed_text += channel_result.raw_text
        return transcribed_text.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _perform_transcription(self, file_path: str) -> str:
        logger.debug(f"Performing transcription for {file_path}")
        model = self._create_recognition_model()
        result = model.transcribe_file(file_path)
        return self._extract_text_from_result(result)

    async def _transcribe_file(
        self,
        file: Union[BytesIO, str],
        file_type: str,
        suffix: str
    ) -> Optional[str]:
        temp_file_path = None
        try:
            logger.info(f"Starting {file_type} transcription with Yandex SpeechKit...")

            if isinstance(file, BytesIO):
                temp_file_path = self._save_bytesio_to_temp(file, suffix=suffix)
                file_path = str(temp_file_path)
            else:
                file_path = file

            transcribed_text = self._perform_transcription(file_path)

            if transcribed_text:
                logger.info(f"{file_type.capitalize()} transcription successful: {len(transcribed_text)} characters")
                return transcribed_text
            else:
                logger.warning(f"{file_type.capitalize()} transcription returned empty text")
                return None

        except Exception as e:
            logger.error(f"Error transcribing {file_type}: {e}", exc_info=True)
            return None

        finally:
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

    async def transcribe_audio(self, audio_file: Union[BytesIO, str]) -> Optional[str]:
        return await self._transcribe_file(audio_file, "audio", ".ogg")

    async def transcribe_video_note(self, video_file: Union[BytesIO, str]) -> Optional[str]:
        return await self._transcribe_file(video_file, "video note", ".mp4")
