import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType

from config import Config

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self):
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

    def _save_bytesio_to_temp(self, audio_data: BytesIO, suffix: str = ".ogg") -> Path:
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp_file:
            audio_data.seek(0)
            tmp_file.write(audio_data.read())
            return Path(tmp_file.name)

    async def transcribe_audio(self, audio_file: Union[BytesIO, str]) -> Optional[str]:
        temp_file_path = None
        try:
            logger.info("Starting audio transcription with Yandex SpeechKit...")

            if isinstance(audio_file, BytesIO):
                temp_file_path = self._save_bytesio_to_temp(audio_file, suffix=".ogg")
                file_path = str(temp_file_path)
            else:
                file_path = audio_file

            model = self._create_recognition_model()

            result = model.transcribe_file(file_path)

 
            transcribed_text = ""
            for channel_result in result:
                if channel_result.normalized_text:
                    transcribed_text += channel_result.normalized_text
                elif channel_result.raw_text:
                    transcribed_text += channel_result.raw_text

            if transcribed_text:
                logger.info(f"Audio transcription successful: {len(transcribed_text)} characters")
                return transcribed_text.strip()
            else:
                logger.warning("Transcription returned empty text")
                return None

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            return None

        finally:
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

    async def transcribe_video_note(self, video_file: Union[BytesIO, str]) -> Optional[str]:
        temp_file_path = None
        try:
            logger.info("Starting video note transcription with Yandex SpeechKit...")

            if isinstance(video_file, BytesIO):
                temp_file_path = self._save_bytesio_to_temp(video_file, suffix=".mp4")
                file_path = str(temp_file_path)
            else:
                file_path = video_file

            model = self._create_recognition_model()

            result = model.transcribe_file(file_path)

            transcribed_text = ""
            for channel_result in result:
                if channel_result.normalized_text:
                    transcribed_text += channel_result.normalized_text
                elif channel_result.raw_text:
                    transcribed_text += channel_result.raw_text

            if transcribed_text:
                logger.info(f"Video note transcription successful: {len(transcribed_text)} characters")
                return transcribed_text.strip()
            else:
                logger.warning("Video note transcription returned empty text")
                return None

        except Exception as e:
            logger.error(f"Error transcribing video note: {e}", exc_info=True)
            return None

        finally:
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
