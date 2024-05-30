from utils import LLMUtils
from configs import OpenAIConfigs
from rich.console import Console
from rich.markdown import Markdown
import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
import base64


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


def preprocess_image(image_link: str):
    """Preprocess the image before sending it to OpenAI.

    Args:
        image_link (str): The image link.

    Returns:
        _type_: _description_
    """

    # Read the image file from disk and resize it
    image = Image.open(image_link)

    # Convert the image to 'RGBA' mode
    if image.mode not in ["RGBA", "LA", "L"]:
        image = image.convert("RGBA")

    width, height = 256, 256
    image = image.resize((width, height))

    # Convert the image to a BytesIO object
    byte_stream = BytesIO()
    image.save(byte_stream, format="PNG")
    byte_array = byte_stream.getvalue()

    # 將位元組數據轉換為圖像對象
    image = Image.open(BytesIO(byte_array))
    image.show()

    return byte_array


def save_image(response: str | None, save_name: str = "variant.png"):
    if response is not None:
        image_data = base64.b64decode(response)
        image = Image.open(BytesIO(image_data))

        save_path = "src/pictures/variant.png"
        image.save(save_path)
        print(f"Image saved to {save_path}")
    else:
        print("No image data received.")


def generate_image(prompt: str):
    """This function generates an image based on the prompt.

    Args:
        prompt (str): The prompt to generate the image.

    Returns:
        _type_: The image URL.
    """

    response = LLMUtils.OPENAI_CLIENT.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="b64_json",
    )
    return response.data[0].b64_json


def variantify_image(image_link: str, number_of_variants: int = 1):
    """Generate variants of an image.

    you can generate multiple variants of an image by providing the number_of_variants.

    Args:
        image_link (str): _description_
        number_of_variants (int, optional): _description_. Defaults to 1.

    Returns:
        _type_: _description_
    """
    byte_array = preprocess_image(image_link)

    response = LLMUtils.OPENAI_CLIENT.images.create_variation(
        image=byte_array,
        n=number_of_variants,
        model="dall-e-2",
        size="256x256",
        response_format="b64_json",
    )
    return response.data[0].b64_json


def modify_image(
    targe_image_link: str,
    mask_image_link: str,
    prompt: str,
    number_of_generations: int = 1,
):
    target_byte_array = preprocess_image(targe_image_link)
    mask_byte_array = preprocess_image(mask_image_link)

    response = LLMUtils.OPENAI_CLIENT.images.edit(
        model="dall-e-2",
        image=target_byte_array,
        mask=mask_byte_array,
        prompt=prompt,
        n=number_of_generations,
        response_format="b64_json",
    )
    return response.data[0].b64_json


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

    text_data = """
    Sure, here is the table in JSON format:

```json
[
    {
        "Name": "John Doe",
        "Age": 29,
        "City": "New York"
    },
    {
        "Name": "Jane Smith",
        "Age": 32,
        "City": "Los Angeles"
    },
    {
        "Name": "Emily Davis",
        "Age": 22,
        "City": "Chicago"
    }
]
```

Here are some examples of how the table might look:

### Example 1:
| Name       | Age | City        |
|------------|-----|-------------|
| John Doe   | 29  | New York    |
| Jane Smith | 32  | Los Angeles |
| Emily Davis| 22  | Chicago     |

### Example 2:
| Name        | Age | City        |
|-------------|-----|-------------|
| John Doe    | 29  | New York    |
| Jane Smith  | 32  | Los Angeles |
| Emily Davis | 22  | Chicago     |

### Example 3:
| Name        | Age | City        |
|-------------|-----|-------------|
| John Doe    | 29  | New York    |
| Jane Smith  | 32  | Los Angeles |
| Emily Davis | 22  | Chicago     |
"""

    # json_match = re.search(
    #     r"json\s*(\[\s*{[^}]+}\s*\])\s*", text_data, re.DOTALL
    # )
    # json_match = re.search(r"json\s*([\s\S]*?)\s*", text_data)

    pattern = re.compile(r"json\n(.*?)\n", re.DOTALL)
    json_match = re.search(r"\[\s*\{.*?\}\s*\]", text_data, re.DOTALL)

    if json_match:
        json_str = json_match.group(0)

        print(f"json_match.group(0): {json_match.group(0)}")
        # print(f"json_match.group(1): {json_match.group(1)}")
        data = json.loads(json_str)
        df = pd.DataFrame(data)
        print(df)
    else:
        print("未找到有效的 JSON 格式數據")

    # response = generate_image("a white siamese cat")
    # save_image(response)

    # response = variantify_image("src/pictures/cat.png")
    # save_image(response)

    # response = modify_image(
    #     "src/pictures/cat.png",
    #     "src/pictures/spot.jpg",
    #     "一隻可愛的小貓坐在九份老街旁邊",
    #     1,
    # )
    # save_image(response)
