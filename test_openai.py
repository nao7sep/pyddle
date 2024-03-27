# Created: 2024-03-27
# Test/sample code for pyddle_openai.py.

import json
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_openai as openai

file_system.make_and_move_to_output_subdirectory()

# GitHub Copilot automatically generated this and I liked it. :)
english_text_for_audio = "Hello, my name is Pyddle. I am a Python library for creating games and applications. I am a work in progress, but I am getting better every day. I am excited to see what you will create with me. Have fun and happy coding!"

def test_audio():
    # Makes audio.

    audio_response = openai.openai_audio_speech_create(
        input=english_text_for_audio,
        model=openai.OpenAiModel.TTS_1_HD,
        voice=openai.OpenAiVoice.NOVA,
        response_format=openai.OpenAiAudioFormat.MP3)

    # Saves the audio to a file.

    audio_file_name = "test_openai_english.mp3"
    openai.openai_save_audio(audio_file_name, audio_response)
    print(f"English audio saved to: {audio_file_name}")

    # Transcribes the audio file.

    transcription = openai.openai_audio_transcriptions_create(
        file_path=audio_file_name,
        model=openai.OpenAiModel.WHISPER_1,
        response_format=openai.OpenAiTranscriptFormat.VERBOSE_JSON)

    # Saves the transcription to a file.

    transcription_file_name = "test_openai_english_transcription.json"
    transcription_json = transcription.model_dump_json(indent=4)
    file_system.write_all_text_to_file(transcription_file_name, transcription_json)
    print(f"English transcription saved to: {transcription_file_name}")

    # Displays the transcription.

    print(f"English transcription: {transcription.text}")

    # Translate the transcription into Japanese.
    # We'll use Chat here, but Chat will be tested later.

    translated_transcription_response = openai.openai_chat_completions_create(
        model=openai.OpenAiModel.GPT_4_TURBO,
        messages=openai.openai_build_messages(
            # Based on my comments, GitHub Copilot generated this.
            user_message=f"Translate the following text into Japanese: {transcription.text}"))

    # Saves the translated transcription to a file.

    translated_transcription_file_name = "test_openai_japanese_translation_by_chat.json"
    translated_transcription_json = translated_transcription_response.model_dump_json(indent=4)
    file_system.write_all_text_to_file(translated_transcription_file_name, translated_transcription_json)
    print(f"Japanese translation by Chat saved to: {translated_transcription_file_name}")

    # Displays the translated transcription.

    translated_transcription_text = openai.openai_extract_first_message(translated_transcription_response)
    print(f"Japanese translation by Chat: {translated_transcription_text}")

    # Makes new audio from the translated transcription.

    translated_audio_response = openai.openai_audio_speech_create(
        input=translated_transcription_text,
        model=openai.OpenAiModel.TTS_1_HD,
        voice=openai.OpenAiVoice.ALLOY,
        response_format=openai.OpenAiAudioFormat.MP3)

    # Saves the translated audio to a file.

    translated_audio_file_name = "test_openai_japanese.mp3"
    openai.openai_save_audio(translated_audio_file_name, translated_audio_response)
    print(f"Japanese audio saved to: {translated_audio_file_name}")

    # Translates the new audio file.

    translation = openai.openai_audio_translations_create(
        file_path=translated_audio_file_name,
        model=openai.OpenAiModel.WHISPER_1,
        response_format=openai.OpenAiTranscriptFormat.VERBOSE_JSON)

    # Saves the translation to a file.

    translation_file_name = "test_openai_english_translation.json"
    translation_json = translation.model_dump_json(indent=4)
    file_system.write_all_text_to_file(translation_file_name, translation_json)
    print(f"English translation saved to: {translation_file_name}")

    # Displays the translation.

    print(f"English translation: {translation.text}")

def compare_original_and_translated_texts():
    translation_file_name = "test_openai_english_translation.json"
    translation_json = file_system.read_all_text_from_file(translation_file_name)
    translation_text = json.loads(translation_json)["text"]

    # Compare the text:

    comparison_response = openai.openai_chat_completions_create(
        model=openai.OpenAiModel.GPT_4_TURBO,
        messages=openai.openai_build_messages(f"Compare the following texts:\n\n{english_text_for_audio}\n\n {translation_text}"))

    # Saves the comparison results to a file.

    comparison_file_name = "test_openai_text_comparison.json"
    comparison_json = comparison_response.model_dump_json(indent=4)
    file_system.write_all_text_to_file(comparison_file_name, comparison_json)
    print(f"Text comparison results saved to: {comparison_file_name}")

    # Displays the comparison results.

    comparison_text = openai.openai_extract_first_message(comparison_response)
    print(f"Text comparison results: {comparison_text}")

# ------------------------------------------------------------------------------
#     Tests
# ------------------------------------------------------------------------------

# Some of the results are saved in: AY04 Testing pyddle_openai.py.json
# You will find the file in the Resources repository's Episodic directory.

test_audio()
compare_original_and_translated_texts()

debugging.display_press_enter_key_to_continue_if_not_debugging()
