from utils import LLMUtils
from configs import OpenAIConfigs
from rich.console import Console
from rich.markdown import Markdown
import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
from openai import OpenAI


def get_response_from_openai(
    prompts_for_system: str, prompt_for_journals_user: str
) -> str | None:
    response = LLMUtils.OPENAI_CLIENT.chat.completions.create(
        model=OpenAIConfigs.OPENAI_GPT_4O_MODEL_NAME,
        messages=[
            {"role": "system", "content": prompts_for_system},
            {"role": "user", "content": prompt_for_journals_user},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def generate_image(prompt: str):

    response = LLMUtils.OPENAI_CLIENT.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    print(response)

    image_url = response.data[0].url
    return image_url


def variantify_image(image_link: str, number_of_variants: int = 1):
    """The function to variantify the image.


    Args:
        image_link (str): _description_

    Returns:
        _type_: _description_
    """

    # Read the image file from disk and resize it
    image = Image.open(image_link)
    width, height = 256, 256
    image = image.resize((width, height))

    # Convert the image to a BytesIO object
    byte_stream = BytesIO()
    image.save(byte_stream, format="PNG")
    byte_array = byte_stream.getvalue()

    response = LLMUtils.OPENAI_CLIENT.images.create_variation(
        image=byte_array, n=number_of_variants, model="dall-e-2", size="256x256"
    )

    print(response)
    return response


if __name__ == "__main__":
    prompt = """
    Convert the following text into a table format with columns 'Name', 'Age', 'City':
    1. John Doe, 29, New York
    2. Jane Smith, 32, Los Angeles
    3. Emily Davis, 22, Chicago

    use json format to represent the table. and give me some examples of the table.
    """

    # response = get_response_from_openai(
    #     "Hello",
    #     prompt,
    # )
    # print(response)

    # json_pattern = re.compile(r"json\s*(.*?)\s*", re.DOTALL)
    # json_match = json_pattern.search(response)
    # print(f"json_match: {json_match}")

    # if json_match:
    #     json_data = json_match.group(1)
    #     data = json.loads(json_data)

    #     df = pd.DataFrame(data)
    #     print(df)

    # image_url = generate_image("a white siamese cat")
    # print(image_url)

    response = modify_image("src/pictures/cat.png")
    print(response)
