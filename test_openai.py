# Created: 2024-03-27
# Test/sample code for pyddle_openai.py.

import json
import traceback

import PIL.Image # pip install pillow
import PIL.ImageDraw

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_errors as perrors
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_openai as openai
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

pfs.make_and_move_to_output_subdirectory("openai")

# GitHub Copilot automatically generated this and I liked it. :)
ENGLISH_TEXT_FOR_AUDIO = "Hello, my name is Pyddle. I am a Python library for creating games and applications. I am a work in progress, but I am getting better every day. I am excited to see what you will create with me. Have fun and happy coding!"

def test_audio():
    # Makes audio.

    audio_response = openai.create_audio_speech(
        input_ = ENGLISH_TEXT_FOR_AUDIO,
        model = openai.Model.TTS_1_HD,
        voice = openai.Voice.NOVA,
        response_format = openai.AudioFormat.MP3)

    # Saves the audio to a file.

    audio_file_name = "test_openai_english.mp3"
    openai.openai_save_audio(audio_file_name, audio_response)
    print(f"English audio saved to: {audio_file_name}")

    # Transcribes the audio file.

    transcription = openai.create_audio_transcription(
        file_path = audio_file_name,
        model = openai.Model.WHISPER_1,
        response_format = openai.TranscriptFormat.VERBOSE_JSON)

    # Saves the transcription to a file.

    transcription_file_name = "test_openai_english_transcription.json"
    transcription_json = transcription.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(transcription_file_name, transcription_json)
    print(f"English transcription saved to: {transcription_file_name}")

    # Displays the transcription.

    print(f"English transcription: {transcription.text}")

    # Translate the transcription into Japanese.
    # We'll use Chat here, but Chat will be tested later.

    translated_transcription_response = openai.create_chat_completions(
        model = openai.Model.GPT_4_TURBO,
        messages = openai.build_messages(
            # Based on my comments, GitHub Copilot generated this.
            user_message = f"Translate the following text into Japanese: {transcription.text}"))

    # Saves the translated transcription to a file.

    translated_transcription_file_name = "test_openai_japanese_translation_by_chat.json"
    translated_transcription_json = translated_transcription_response.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(translated_transcription_file_name, translated_transcription_json)
    print(f"Japanese translation by Chat saved to: {translated_transcription_file_name}")

    # Displays the translated transcription.

    translated_transcription_text = openai.extract_first_message(translated_transcription_response)
    print(f"Japanese translation by Chat: {translated_transcription_text}")

    # Makes new audio from the translated transcription.

    translated_audio_response = openai.create_audio_speech(
        input_ = translated_transcription_text,
        model = openai.Model.TTS_1_HD,
        voice = openai.Voice.ALLOY,
        response_format = openai.AudioFormat.MP3)

    # Saves the translated audio to a file.

    translated_audio_file_name = "test_openai_japanese.mp3"
    openai.openai_save_audio(translated_audio_file_name, translated_audio_response)
    print(f"Japanese audio saved to: {translated_audio_file_name}")

    # Translates the new audio file.

    translation = openai.create_audio_translation(
        file_path = translated_audio_file_name,
        model = openai.Model.WHISPER_1,
        response_format = openai.TranscriptFormat.VERBOSE_JSON)

    # Saves the translation to a file.

    translation_file_name = "test_openai_english_translation.json"
    translation_json = translation.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(translation_file_name, translation_json)
    print(f"English translation saved to: {translation_file_name}")

    # Displays the translation.

    print(f"English translation: {translation.text}")

def compare_original_and_translated_texts():
    translation_file_name = "test_openai_english_translation.json"
    translation_json = pfs.read_all_text_from_file(translation_file_name)
    translation_text = json.loads(translation_json)["text"]

    # Compare the text:

    comparison_response = openai.create_chat_completions(
        model = openai.Model.GPT_4_TURBO,
        messages = openai.build_messages(f"Compare the following texts:\n\n{ENGLISH_TEXT_FOR_AUDIO}\n\n {translation_text}"))

    # Saves the comparison results to a file.

    comparison_file_name = "test_openai_text_comparison.json"
    comparison_json = comparison_response.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(comparison_file_name, comparison_json)
    print(f"Text comparison results saved to: {comparison_file_name}")

    # Displays the comparison results.

    comparison_text = openai.extract_first_message(comparison_response)

    print("Text comparison results:")

    for line in pstring.splitlines(comparison_text):
        pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

def test_chat():
    # Converse to get 3 different household tools.

    messages: list[dict[str, str]] = []

    common_system_message = "No affirmative interjections such as 'certainly'."
    openai.add_system_message(messages, common_system_message)

    different_tool_prompt = "Talk about one household tool we havent discussed yet."
    different_tool_responses = []
    different_tool_answers = []

    for index in range(3):
        openai.add_user_message(messages, different_tool_prompt)

        different_tool_responses.append(openai.create_chat_completions(
            model = openai.Model.GPT_4_TURBO,
            messages = messages))

        different_tool_answers.append(openai.extract_first_message(different_tool_responses[index]))
        openai.add_assistant_message(messages, different_tool_answers[index])

    # Saves the responses to files.

    for index in range(3):
        different_tool_file_name = f"test_openai_tool_{index + 1}.json"
        different_tool_json = different_tool_responses[index].model_dump_json(indent = 4)
        pfs.write_all_text_to_file(different_tool_file_name, different_tool_json)
        print(f"Tool {index + 1} saved to: {different_tool_file_name}")

    # Displays the answers.

    for index in range(3):
        print(f"Tool {index + 1}:")

        for line in pstring.splitlines(different_tool_answers[index]):
            pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

    # Summarizes the answers.

    messages = []

    openai.add_system_message(messages, common_system_message)

    summarization_responses = []
    summarization_answers = []

    for index in range(3):
        summarization_prompt = f"Summarize the following text: {different_tool_answers[index]}"
        openai.add_user_message(messages, summarization_prompt)

        summarization_responses.append(openai.create_chat_completions(
            model = openai.Model.GPT_4_TURBO,
            messages = messages,
            max_tokens = 100)) # Limited length.
            # As a result, the summaries will be incomplete.
            # "finish_reason" will be set to "length".

        summarization_answers.append(openai.extract_first_message(summarization_responses[index]))
        messages.pop()

    # Saves the summarization responses to files.

    for index in range(3):
        summarization_file_name = f"test_openai_tool_{index + 1}_summary.json"
        summarization_json = summarization_responses[index].model_dump_json(indent = 4)
        pfs.write_all_text_to_file(summarization_file_name, summarization_json)
        print(f"Tool {index + 1} summary saved to: {summarization_file_name}")

    # Displays the summaries.

    for index in range(3):
        print(f"Tool {index + 1} summary:")

        for line in pstring.splitlines(summarization_answers[index]):
            pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

    # Asks to select the most suitable tool based on the summaries.

    messages = []

    openai.add_system_message(messages, common_system_message)

    for index in range(3):
        openai.add_user_message(messages, different_tool_prompt)
        # Sometimes, the summary is focused on the speaker's intention rather than the content, but it works just fine.
        openai.add_assistant_message(messages, summarization_answers[index])

    suitable_tool_prompt = "Out of the 3, which tool would be most suitable for a picnic and why?"
    openai.add_user_message(messages, suitable_tool_prompt)

    suitable_tool_response = openai.create_chat_completions(
        model = openai.Model.GPT_4_TURBO,
        messages = messages,
        stream = True)

    # Displays the chunks as they come in.

    print("Suitable tool:")

    needs_indentation = True

    chunk_models = []

    for chunk in suitable_tool_response: # pylint: disable = not-an-iterable
        # The internally called method returns ChatCompletion or Stream[ChatCompletionChunk] depending on "stream".
        # Iterating over the response object is correct:
        # https://cookbook.openai.com/examples/how_to_stream_completions

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
                    print(pstring.LEVELED_INDENTS[1], end = "")
                    needs_indentation = False

            print(chunk_str, end = "")

        chunk_models.append(chunk.model_dump())

    # Should work like WriteLine.
    print()

    # Saves the chunks to a file.

    suitable_tool_file_name = "test_openai_suitable_tool.json"
    suitable_tool_json = json.dumps(chunk_models, indent = 4)
    pfs.write_all_text_to_file(suitable_tool_file_name, suitable_tool_json)
    print(f"Suitable tool saved to: {suitable_tool_file_name}")

# Technically, Vision is a part of Chat, but it would be more efficient to test it in the context of Images.
def test_images_and_vision():
    # Asks for 3 random prompts for image generation.

    prompt_generation_response = openai.create_chat_completions(
        model = openai.Model.GPT_4_TURBO,
        messages = openai.build_messages(
            # Generated by ChatGPT:
            user_message = "Craft three unique prompts for image generation, each on a separate line without leading numbers or indentation, and no trailing white space."))

    prompt_generation_file_name = "test_openai_image_prompts.json"
    prompt_generation_json = prompt_generation_response.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(prompt_generation_file_name, prompt_generation_json)
    print(f"Image prompts saved to: {prompt_generation_file_name}")

    prompt_generation_answer = openai.extract_first_message(prompt_generation_response)
    # Sometimes, I still get 5 lines containing 3 prompts and 2 empty lines.
    image_generation_prompts = [line for line in pstring.splitlines(prompt_generation_answer) if line]

    print("Image prompts:")

    for index, prompt in enumerate(image_generation_prompts):
        pconsole.print(f"Prompt {index + 1}: {prompt}", indents = pstring.LEVELED_INDENTS[1])

    # Generates images from the prompts.

    image_generation_responses = []
    image_generation_file_names = []

    for index in range(3):
        image_generation_responses.append(openai.generate_images(
            model = openai.Model.DALL_E_3,
            prompt = image_generation_prompts[index],
            quality = openai.ImageQuality.HD))
            # => The default size (1024x1024) will be applied.

        image_generation_file_names.append(f"test_openai_image_{index + 1}.png")
        openai.save_images(image_generation_file_names[index], image_generation_responses[index])
        print(f"Image {index + 1} saved to: {image_generation_file_names[index]}")

    # Generates RGBA images, masking certain areas for editing.

    masked_image_file_names = []

    for index in range(3):
        rgb_image = PIL.Image.open(image_generation_file_names[index])

        if not pstring.equals_ignore_case(rgb_image.format, "PNG"):
            raise RuntimeError(f"Image {index + 1} is not in PNG format.")

        if pstring.equals_ignore_case(rgb_image.mode, "RGBA"):
            raise RuntimeError(f"Image {index + 1} is already in RGBA mode.")

        rgba_image = rgb_image.convert("RGBA")
        width, height = rgba_image.size

        # Makes a luminance-only, one-channel, black-and-white image.
        # Makes a drawing object to draw on the image.

        # We could instead extract each pixel by their coordinates and update the alpha channel manually.
        # But it should be way faster to let the underlying C-based binary do the work by calling some of the dedicated drawing methods.

        alpha = PIL.Image.new("L", rgba_image.size, 255) # When interpreted as an alpha channel, 0 is transparent and 255 is opaque.
        # So, we are starting with an alpha-channel-only image, which would not affect the visibility of the RGB channels at all.
        draw = PIL.ImageDraw.Draw(alpha)

        # Draws transparent objects on the alpha channel.
        # (0, 0) is the top-left corner.

        if index == 0:
            # xy – Two points to define the bounding box.
            # Sequence of either [(x0, y0), (x1, y1)] or [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
            # The bounding box is inclusive of both endpoints.
            # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html

            draw.rectangle([(0, 0), (width // 2, height // 2)], fill = 0)
            draw.rectangle([(width // 2, height // 2), (width, height)], fill = 0)

        elif index == 1:
            draw.polygon([(0, 0), (0, height), (width, height)], fill = 0)

        else:
            margin = width // 6 # The diameter of the ellipse will be 2/3 of the image width.
            draw.ellipse([(margin, margin), (width - margin, height - margin)], fill = 0)

        # Combines the RGB and alpha channels.
        rgba_image.putalpha(alpha)

        # Additional note: The files generated by OpenAI had exactly the same file lengths
        #     most likely because they were compressed in a manner that's most suitable for streaming transfer.
        # Then, I masked them and saw significantly different file lengths.
        # I had to make sure that the differences occurred because of the presumably different compression method used internally
        #     rather than my unintentionally dropping some data from the images.
        # I made one all-opaque image and "putalpha"-ed it to the already masked images.
        # I successfully got the images back.
        # So, the masked images generated here do have the original RGB data.

        masked_image_file_names.append(image_generation_file_names[index].replace(".png", "_masked.png"))
        rgba_image.save(masked_image_file_names[index])
        print(f"Masked image {index + 1} saved to: {masked_image_file_names[index]}")

    # Edits the images.

    image_editing_responses = []
    edited_image_file_names = []

    for index in range(3):
        image_editing_responses.append(openai.edit_image(
            input_file_path = masked_image_file_names[index],
            model = openai.Model.DALL_E_2,
            # Generated by ChatGPT:
            prompt = "Using the context provided by the unmasked portions of the image, completely reimagine and recreate the content within the masked area to blend seamlessly and coherently with its surroundings."))

        edited_image_file_names.append(masked_image_file_names[index].replace("_masked.png", "_edited.png"))
        openai.save_images(edited_image_file_names[index], image_editing_responses[index])
        print(f"Edited image {index + 1} saved to: {edited_image_file_names[index]}")

    # Generates variations.

    image_variation_responses = []

    for index in range(3):
        image_variation_responses.append(openai.create_image_variations(
            input_file_path = image_generation_file_names[index],
            model = openai.Model.DALL_E_2))

        variation_file_name = image_generation_file_names[index].replace(".png", "_variation.png")
        openai.save_images(variation_file_name, image_variation_responses[index])
        print(f"Image variation {index + 1} saved to: {variation_file_name}")

    # Asks Vision about each image.

    vision_each_image_responses = []
    vision_each_image_answers = []

    for index in range(3):
        vision_each_image_responses.append(openai.create_chat_completions(
            model = openai.Model.GPT_4_VISION,
            messages = openai.build_messages_for_vision(
                image_file_paths = [image_generation_file_names[index]],
                user_message = "What do you see in this image?")))

        vision_each_image_file_name = f"test_openai_image_{index + 1}_vision.json"
        vision_each_image_json = vision_each_image_responses[index].model_dump_json(indent = 4)
        pfs.write_all_text_to_file(vision_each_image_file_name, vision_each_image_json)
        print(f"Vision results for image {index + 1} saved to: {vision_each_image_file_name}")

        vision_each_image_answers.append(openai.extract_first_message(vision_each_image_responses[index]))

        print(f"Vision results for image {index + 1}:")

        for line in pstring.splitlines(vision_each_image_answers[index]):
            pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

    # Asks Vision about 3 images at once.

    vision_all_images_response = openai.create_chat_completions(
        model = openai.Model.GPT_4_VISION,
        messages = openai.build_messages_for_vision(
            image_file_paths = image_generation_file_names,
            user_message = "What do you find in common among these images?"))
            # => I once got a response like: I'm sorry, I can't help with identifying or making assumptions about these images.

    vision_all_images_file_name = "test_openai_images_vision.json"
    vision_all_images_json = vision_all_images_response.model_dump_json(indent = 4)
    pfs.write_all_text_to_file(vision_all_images_file_name, vision_all_images_json)
    print(f"Vision results for all images saved to: {vision_all_images_file_name}")

    vision_all_images_answer = openai.extract_first_message(vision_all_images_response)

    # Added: I've implemented multiline output after the results have been saved.
    # New results would look slightly different from the old ones.

    print("Vision results for all images:")

    for line in pstring.splitlines(vision_all_images_answer):
        pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

# ------------------------------------------------------------------------------
#     Tests
# ------------------------------------------------------------------------------

# Some of the results are saved in: AY04 Testing pyddle_openai.py.json
# You will find the file in the Resources repository's Episodic directory.

try:
    test_audio()
    compare_original_and_translated_texts()

    test_chat()

    test_images_and_vision()

except Exception: # pylint: disable = broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
