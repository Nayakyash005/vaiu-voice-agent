import asyncio
import json
import logging
import re
import urllib.request

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    STTContextOptions,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
)
from livekit.agents.llm import StopResponse
from livekit.plugins import ai_coustics

from phone_parser import (
    has_phone_number_correction,
    is_valid_phone_number,
    parse_confirmation,
    parsePhoneNumber,
)

logger = logging.getLogger("agent")

load_dotenv(".env.local")

PHONE_API_URL = "http://127.0.0.1:8000/api/phone"
_ENGLISH_WORDS = {
    "and",
    "confirm",
    "correct",
    "double",
    "eight",
    "five",
    "four",
    "hello",
    "is",
    "it",
    "my",
    "nine",
    "number",
    "o",
    "oh",
    "one",
    "phone",
    "please",
    "right",
    "seven",
    "six",
    "the",
    "three",
    "triple",
    "two",
    "wait",
    "yes",
    "zero",
}
_ROMANIZED_HINDI_WORDS = {
    "aath",
    "bilkul",
    "chaar",
    "chhe",
    "do",
    "ek",
    "galat",
    "haan",
    "han",
    "matlab",
    "mera",
    "nahi",
    "nahin",
    "nau",
    "paanch",
    "saat",
    "sahi",
    "shunya",
    "sifar",
    "teen",
    "suniye",
    "rukho",
    "ruko",
    "dobara",
    "phir",
    "se",
}


def detect_transcript_language(transcript: str) -> str:
    """Classify the collected transcript as English, Hindi, or mixed."""
    tokens = re.findall(r"[a-z]+|[\u0900-\u097f]+", transcript.casefold())
    has_devanagari = any(re.search(r"[\u0900-\u097f]", token) for token in tokens)
    has_romanized_hindi = any(token in _ROMANIZED_HINDI_WORDS for token in tokens)
    has_hindi = has_devanagari or has_romanized_hindi
    has_english = any(token in _ENGLISH_WORDS for token in tokens)

    if has_hindi and has_english:
        return "mixed"
    if has_hindi:
        return "hi"
    return "en"


class PhoneNumberAgent(Agent):
    """Collect and confirm a mobile number without using an LLM."""

    def __init__(self) -> None:
        super().__init__(
            instructions="Collect a 10-digit mobile number and confirm it.",
            llm=None,
        )
        self._awaiting_confirmation = False
        self._pending_phone_number: str | None = None
        self._collected_digits = ""
        self._transcript_parts: list[str] = []
        self.confirmed_phone_number: str | None = None
        self._save_attempted = False

    async def on_enter(self) -> None:
        await self.session.say("Hello! Please tell me your 10-digit mobile number.")

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        transcript = new_message.text_content or ""

        if self.confirmed_phone_number is not None:
            response_text = "Your number has already been confirmed. Thank you."
        else:
            answer = parse_confirmation(transcript)
            if self._awaiting_confirmation and answer == "yes":
                self.confirmed_phone_number = self._pending_phone_number
                self._pending_phone_number = None
                self._awaiting_confirmation = False
                await self._save_confirmed_phone_number()
                response_text = "Thank you. Your number has been confirmed."
            elif self._awaiting_confirmation and answer == "no":
                self._pending_phone_number = None
                self._awaiting_confirmation = False
                self._collected_digits = ""
                response_text = "Okay. Please repeat your 10-digit mobile number."
            else:
                correction = has_phone_number_correction(transcript)
                if correction:
                    self._collected_digits = ""
                    self._pending_phone_number = None
                    self._awaiting_confirmation = False

                if self._awaiting_confirmation:
                    response_text = (
                        "Please say yes if the number is correct, or no to repeat it."
                    )
                else:
                    if transcript.strip():
                        self._transcript_parts.append(transcript.strip())
                    digits = parsePhoneNumber(transcript)
                    if digits is None:
                        if correction:
                            response_text = (
                                "Okay. Please continue with the corrected number."
                            )
                        elif self._collected_digits:
                            remaining = 10 - len(self._collected_digits)
                            response_text = (
                                f"I have {len(self._collected_digits)} digits. "
                                f"Please continue with the remaining {remaining}."
                            )
                        else:
                            response_text = (
                                "I couldn't understand those digits. Please tell me "
                                "your 10-digit mobile number."
                            )
                    else:
                        self._collected_digits += digits
                        if len(self._collected_digits) < 10:
                            remaining = 10 - len(self._collected_digits)
                            response_text = (
                                f"I have {len(self._collected_digits)} digits. "
                                f"Please continue with the remaining {remaining}."
                            )
                        elif not is_valid_phone_number(self._collected_digits):
                            self._collected_digits = ""
                            response_text = (
                                "That isn't a valid 10-digit mobile number. "
                                "Please repeat the full number."
                            )
                        else:
                            self._pending_phone_number = self._collected_digits
                            self._collected_digits = ""
                            self._awaiting_confirmation = True
                            spoken_digits = ", ".join(self._pending_phone_number)
                            response_text = (
                                f"I heard {spoken_digits}. Is that correct? "
                                "Please say yes or no."
                            )

        await self.session.say(response_text)
        raise StopResponse()

    async def _save_confirmed_phone_number(self) -> None:
        if self._save_attempted or self.confirmed_phone_number is None:
            return

        self._save_attempted = True
        payload = {
            "rawTranscript": " ".join(self._transcript_parts),
            "parsedNumber": self.confirmed_phone_number,
            "language": detect_transcript_language(" ".join(self._transcript_parts)),
        }
        request = urllib.request.Request(
            PHONE_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        def send_request() -> None:
            with urllib.request.urlopen(request, timeout=5) as response:
                response.read()

        try:
            await asyncio.to_thread(send_request)
        except Exception:
            logger.exception("Failed to save confirmed phone number to the API")


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(
            model="assemblyai/universal-3-6-pro",
            extra_kwargs={"min_turn_silence": 4000, "max_turn_silence": 4000},
        ),
        stt_context_options=STTContextOptions(
            keyterms=["mobile number"],
            keyterm_detection={"enabled": True},
        ),
        tts=inference.TTS(
            model="fishaudio/s2.1-pro", voice="fa4c9eb3dccc4806b382b40d61c6b10a"
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection="stt",
            endpointing={"min_delay": 0, "max_delay": 4.0},
            interruption={"mode": "adaptive"},
        ),
        expressive=True,
    )

    await session.start(
        agent=PhoneNumberAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
