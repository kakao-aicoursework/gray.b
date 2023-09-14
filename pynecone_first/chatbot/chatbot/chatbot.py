"""Welcome to Pynecone! This file outlines the steps to create a basic app."""

# Import pynecone.
import openai
import os
from datetime import datetime

import pynecone as pc
from pynecone.base import Base


openai.api_key = ""


parallel_example = {
    "한국어": ["오늘 날씨 어때", "딥러닝 기반의 AI기술이 인기를끌고 있다."],
    "영어": ["How is the weather today", "Deep learning-based AI technology is gaining popularity."],
    "일본어": ["今日の天気はどうですか", "ディープラーニングベースのAIテクノロジーが人気を集めています。"]
}


def translate_text_using_text_davinci(text, trg_lang) -> str:
    response = openai.Completion.create(engine="text-davinci-003",
                                        prompt=f"Translate the following text to {trg_lang}: {text}",
                                        max_tokens=200,
                                        n=1,
                                        temperature=1
                                        )
    translated_text = response.choices[0].text.strip()
    return translated_text


def translate_text_using_chatgpt(text, trg_lang) -> str:
    # fewshot 예제를 만들고
    def build_fewshot(trg_lang):
        korean_examples = parallel_example["한국어"]
        english_examples = parallel_example["영어"]
        japanese_examples = parallel_example["일본어"]
        trg_examples = parallel_example[trg_lang]

        fewshot_messages = []

        for korean, english, japanese, trg in zip(korean_examples, english_examples, japanese_examples, trg_examples):
            if trg_lang == "한국어":
                fewshot_messages.append({"role": "user", "content": english})
                fewshot_messages.append({"role": "assistant", "content": f"{korean}"})
                fewshot_messages.append({"role": "user", "content": japanese})
                fewshot_messages.append({"role": "assistant", "content": f"{korean}"})
            elif trg_lang == "영어":
                fewshot_messages.append({"role": "user", "content": korean})
                fewshot_messages.append({"role": "assistant", "content": f"{english}"})    
                fewshot_messages.append({"role": "user", "content": japanese})
                fewshot_messages.append({"role": "assistant", "content": f"{english}"})    
            else:    
                fewshot_messages.append({"role": "user", "content": korean})
                fewshot_messages.append({"role": "assistant", "content": f"{japanese}"})
                fewshot_messages.append({"role": "user", "content": english})
                fewshot_messages.append({"role": "assistant", "content": f"{japanese}"})
            
            

        return fewshot_messages

    # system instruction 만들고
    system_instruction = f"assistant는 번역 챗봇으로서 동작한다. 사용자가 번역 요청이 들어 온다면. {trg_lang}로 적절하게 번역한다. 번역 요청이 들어온다면 쌍다움표를 양끝에 붙여서 출력한다"

    # messages를만들고
    fewshot_messages = build_fewshot(trg_lang)

    messages = [{"role": "system", "content": system_instruction},
                *fewshot_messages,
                {"role": "user", "content": text}
                ]
    
    print("-----")
    print(messages)
    print("-----")

    # API 호출
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=messages)
    translated_text = response['choices'][0]['message']['content']
    # Return
    return translated_text


class Message(Base):
    original_text: str
    text: str
    created_at: str
    to_lang: str


class State(pc.State):
    """The app state."""

    text: str = ""
    messages: list[Message] = []
    trg_lang: str = "영어"

    @pc.var
    def output(self) -> str:
        if not self.text.strip():
            return "Translations will appear here."
        translated = translate_text_using_chatgpt(
            self.text, trg_lang=self.trg_lang)
        return translated

    def post(self):
        self.messages = self.messages + [
            Message(
                original_text=self.text,
                text=self.output,
                created_at=datetime.now().strftime("%B %d, %Y %I:%M %p"),
                to_lang=self.trg_lang,
            )
        ]


# Define views.


def header():
    """Basic instructions to get started."""
    return pc.box(
        pc.text("GPT Translator Chatbot 🗺", font_size="2rem"),
        pc.text(
            "Translate things and post them as messages!",
            margin_top="0.5rem",
            color="#666",
        ),
    )


def down_arrow():
    return pc.vstack(
        pc.icon(
            tag="arrow_down",
            color="#666",
        )
    )


def text_box(text):
    return pc.text(
        text,
        background_color="#fff",
        padding="1rem",
        border_radius="8px",
    )


def message(message):
     return pc.box(
        pc.box(
            pc.text(
                message.original_text,
                bg="#f1f1f1",
                display="inline-block", 
                p="4", 
                border_radius="xl", 
                max_w="30em"
            ),
            text_align="right",
            margin_top="1em",
        ),
        pc.box(
            pc.text(
                message.text,
                bg="#f1f1f1",
                display="inline-block", 
                p="4", 
                border_radius="xl", 
                max_w="30em"
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )

def chat():
    return pc.vstack(
        pc.box(pc.foreach(State.messages, message)),
        py="8",
        flex="1",
        width="100%",
        max_w="3xl",
        padding_x="4",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )

def smallcaps(text, **kwargs):
    return pc.text(
        text,
        font_size="0.7rem",
        font_weight="bold",
        text_transform="uppercase",
        letter_spacing="0.05rem",
        **kwargs,
    )


def output():
    return pc.box(
        pc.box(
            smallcaps(
                "Output",
                color="#aeaeaf",
                background_color="white",
                padding_x="0.1rem",
            ),
            position="absolute",
            top="-0.5rem",
        ),
        pc.text(State.output),
        padding="1rem",
        border="1px solid #eaeaef",
        margin_top="1rem",
        border_radius="8px",
        position="relative",
    )


def index():
    """The main view."""
    return pc.container(
        pc.center(
            pc.vstack(
                header(),
                chat(),
                pc.input(
                    placeholder="Text to translate",
                    on_blur=State.set_text,
                    margin_top="1rem",
                    border_color="#eaeaef"
                ),
                pc.hstack(
                    pc.select(
                        list(parallel_example.keys()),
                        value=State.trg_lang,
                        placeholder="Select a language",
                        on_change=State.set_trg_lang,
                        margin_top="1rem",
                    ),    
                    pc.button("Post", on_click=State.post, margin_top="1rem"),
                )
            ),
            shadow="lg",
            padding="1em",
            border_radius="lg",
            width="100%",
        ),
         width="100%",
    )


# Add state and page to the app.
app = pc.App(state=State)
app.add_page(index, title="Translator")
app.compile()
