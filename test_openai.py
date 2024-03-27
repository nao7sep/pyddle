# Created: 2024-03-27
# Test/sample code for pyddle_openai.py.

import json
import pyddle_console as console
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_openai as openai
import pyddle_string as string

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
    # The text usually contains line breaks, but I wont indent the lines.
    # The results have been saved to a file.
    print(f"Text comparison results: {comparison_text}")

def test_chat():
    # Converse to get 3 different household tools.

    messages = []

    common_system_message = "No affirmative interjections such as 'certainly'."
    openai.openai_add_system_message(messages, common_system_message)

    different_tool_prompt = "Talk about one household tool we havent discussed yet."
    different_tool_responses = []
    different_tool_answers = []

    for index in range(3):
        openai.openai_add_user_message(messages, different_tool_prompt)

        different_tool_responses.append(openai.openai_chat_completions_create(
            model=openai.OpenAiModel.GPT_4_TURBO,
            messages=messages))

        different_tool_answers.append(openai.openai_extract_first_message(different_tool_responses[index]))
        openai.openai_add_assistant_message(messages, different_tool_answers[index])

    # Saves the responses to files.

    for index in range(3):
        different_tool_file_name = f"test_openai_tool_{index + 1}.json"
        different_tool_json = different_tool_responses[index].model_dump_json(indent=4)
        file_system.write_all_text_to_file(different_tool_file_name, different_tool_json)
        print(f"Tool {index + 1} saved to: {different_tool_file_name}")

    # Displays the answers.

    for index in range(3):
        print(f"Tool {index + 1}:")

        for line in string.splitlines(different_tool_answers[index]):
            console.print(line, indents=string.leveledIndents[1])

    # Summarizes the answers.

    messages = []

    openai.openai_add_system_message(messages, common_system_message)

    summarization_responses = []
    summarization_answers = []

    for index in range(3):
        summarization_prompt = f"Summarize the following text: {different_tool_answers[index]}"
        openai.openai_add_user_message(messages, summarization_prompt)

        summarization_responses.append(openai.openai_chat_completions_create(
            model=openai.OpenAiModel.GPT_4_TURBO,
            messages=messages,
            max_tokens=100)) # Limited length.

        summarization_answers.append(openai.openai_extract_first_message(summarization_responses[index]))
        messages.pop()

    # Saves the summarization responses to files.

    for index in range(3):
        summarization_file_name = f"test_openai_tool_{index + 1}_summary.json"
        summarization_json = summarization_responses[index].model_dump_json(indent=4)
        file_system.write_all_text_to_file(summarization_file_name, summarization_json)
        print(f"Tool {index + 1} summary saved to: {summarization_file_name}")

    # Displays the summaries.

    for index in range(3):
        print(f"Tool {index + 1} summary:")

        for line in string.splitlines(summarization_answers[index]):
            console.print(line, indents=string.leveledIndents[1])

    # Asks to select the most suitable tool based on the summaries.

    messages = []

    openai.openai_add_system_message(messages, common_system_message)

    for index in range(3):
        openai.openai_add_user_message(messages, different_tool_prompt)
        # Sometimes, the summary is focused on the speaker's intention rather than the content, but it works just fine.
        openai.openai_add_assistant_message(messages, summarization_answers[index])

    suitable_tool_prompt = "Out of the 3, which tool would be most suitable for a picnic and why?"
    openai.openai_add_user_message(messages, suitable_tool_prompt)

    suitable_tool_response = openai.openai_chat_completions_create(
        model=openai.OpenAiModel.GPT_4_TURBO,
        messages=messages,
        stream=True)

    # Displays the chunks as they come in.

    print("Suitable tool:")

    needs_indentation = True

    chunk_models = []

    for chunk in suitable_tool_response:
        # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_chunk.py
        # https://github.com/openai/openai-python/blob/main/src/openai/_models.py

        chunk_str = chunk.choices[0].delta.content

        # Tested: 2024-03-27

        # The first chunk's content is "".
        # Then, line breaks come out as ".\n\n" as far as I have seen.
        # The last chunk's content is None.

        # In production code, we'd need a buffered chunks parser.
        # Here, I believe the following implementation is good enough for now.

        if chunk_str:
            if chunk_str.endswith("\n"):
                needs_indentation = True

            else:
                if needs_indentation:
                    print(string.leveledIndents[1], end="")
                    needs_indentation = False

            print(chunk_str, end="")

        chunk_models.append(chunk.model_dump())

    # Should work like WriteLine.
    print()

    # Saves the chunks to a file.

    suitable_tool_file_name = "test_openai_suitable_tool.json"
    suitable_tool_json = json.dumps(chunk_models, indent=4)
    file_system.write_all_text_to_file(suitable_tool_file_name, suitable_tool_json)
    print(f"Suitable tool saved to: {suitable_tool_file_name}")

# ------------------------------------------------------------------------------
#     Tests
# ------------------------------------------------------------------------------

# Some of the results are saved in: AY04 Testing pyddle_openai.py.json
# You will find the file in the Resources repository's Episodic directory.

# test_audio()
# compare_original_and_translated_texts()

test_chat()

debugging.display_press_enter_key_to_continue_if_not_debugging()
