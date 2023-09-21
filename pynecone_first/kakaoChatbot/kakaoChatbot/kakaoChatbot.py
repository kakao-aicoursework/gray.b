import pynecone as pc
from pynecone.base import Base
from langchain import LLMChain
from langchain.chains import ConversationChain, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    SystemMessage
)

import os
from datetime import datetime
os.environ["OPENAI_API_KEY"] = ""

BUG_STEP1_PROMPT_TEMPLATE = "./bug_analyze.txt"
BUG_STEP2_PROMPT_TEMPLATE = "./bug_solution.txt"
ENHANCE_STEP1_PROMPT_TEMPLATE = "./enhancement_say_thanks.txt"
INTENT_LIST_TXT = "./intent_list.txt"

DATA_KAKAO_SINK = "./project_data_카카오싱크.txt"
DATA_KAKAO_SOCIAL = "./project_data_카카오소셜.txt"
DATA_KAKAO_TALK_CAHNNEL = "./project_data_카카오톡채널.txt"
INTENT_PROMPT_TEMPLATE = "./parse_intent.txt"



def read_prompt_template(file_path: str) -> str:
    with open(file_path, "r") as f:
        prompt_template = f.read()

    return prompt_template

def create_chain(llm, template_path, output_key):
    return LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            template=read_prompt_template(template_path)
        ),
        output_key=output_key,
        verbose=True,
    )


llm = ChatOpenAI(temperature=0.8,
                  model_name='gpt-3.5-turbo-16k',
                  max_tokens=1024)
bug_step1_chain = create_chain(
    llm=llm,
    template_path=BUG_STEP1_PROMPT_TEMPLATE,
    output_key="bug_analysis",
)
bug_step2_chain = create_chain(
    llm=llm,
    template_path=BUG_STEP2_PROMPT_TEMPLATE,
    output_key="output",
)
enhance_step1_chain = create_chain(
    llm=llm,
    template_path=ENHANCE_STEP1_PROMPT_TEMPLATE,
    output_key="output",
)
parse_intent_chain = create_chain(
    llm=llm,
    template_path=INTENT_PROMPT_TEMPLATE,
    output_key="intent",
)

default_chain = ConversationChain(llm=llm, output_key="output")

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

CHROMA_PERSIST_DIR = "./chroma"
CHROMA_COLLECTION_NAME = "kakao-bot"

_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=OpenAIEmbeddings(),
    collection_name=CHROMA_COLLECTION_NAME,
)
_retriever = _db.as_retriever()

def query_db(query: str, use_retriever: bool = False) -> list[str]:
    if use_retriever:
        docs = _retriever.get_relevant_documents(query)
    else:
        docs = _db.similarity_search(query)

    str_docs = [doc.page_content for doc in docs]
    return str_docs

def gernerate_answer(user_message) -> str:
    context = dict(user_message=user_message)
    context["input"] = f"""{context["user_message"]}
    \n
    {read_prompt_template(DATA_KAKAO_SINK)}\n
    {read_prompt_template(DATA_KAKAO_SOCIAL)}\n
    {read_prompt_template(DATA_KAKAO_TALK_CAHNNEL)}"
    """
    context["intent_list"] = read_prompt_template(INTENT_LIST_TXT)
    
    print("*"*200)
    print(context)
    print("*"*200)

    # intent = parse_intent_chain(context)["intent"]
    intent = parse_intent_chain.run(context)

    if intent == "bug":
        context["related_documents"] = query_db(context["user_message"])

        answer = ""
        for step in [bug_step1_chain, bug_step2_chain]:
            context = step(context)
            answer += context[step.output_key]
            answer += "\n\n"
    elif intent == "enhancement":
        answer = enhance_step1_chain.run(context)
    else:
        answer = default_chain.run(context["user_message"])

    return answer

# content = open('./project_data_카카오싱크.txt', 'r').read()

# system_message = f"""assistant는 카카오 API를 설명하는 챗봇으로서 동작한다. 

# {content}

# 카카오 싱크 내용을 참고하여 사용법의 설명문을 작성해라 줄바꿈을 통해 가독성이 높게 출력해주세요.

# """
# system_message_prompt = SystemMessage(content=system_message)

# human_template = ("{question}")

# human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
# chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# chain = LLMChain(llm=llm, prompt=chat_prompt)

class Message(Base):
    original_text: str
    text: str
    created_at: str

class State(pc.State):
    """The app state."""

    question: str = ""
    messages: list[Message] = []

    is_working: bool = False
    

    async def handle_submit(self, form_data):
        self.is_working = True
        self.question = form_data['question']

        self.messages = self.messages + [
            Message(
                original_text=self.question,
                text=gernerate_answer(self.question),
                created_at=datetime.now().strftime("%B %d, %Y %I:%M %p"),
            )
        ]

        self.is_working = False
        
    def clear_input(self):
        self.question = "" 

# Define views.
def header():
    """Basic instructions to get started."""
    return pc.box(
        pc.text("Kakao Chatbot 🗺", font_size="2rem"),
        pc.text(
            "Translate things and post them as messages!",
            margin_top="0.5rem",
            color="#666",
        ),
    )
    
def message(message):
     return pc.box(
        pc.box(
            pc.text(
                message.original_text,
                bg="#d1eaf0",
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
    

def index() -> pc.Component:
    return pc.container(
        pc.center(
            pc.form(
            pc.vstack(
                header(),
                chat(),
                pc.input(
                    placeholder="Text to translate",
                    on_blur=State.set_question,
                    margin_top="1rem",
                    border_color="#eaeaef",
                    id="question"
                ),
                pc.hstack(
                    pc.button("Post", type_="submit", margin_top="1rem"),
                )
            ),
            on_submit=State.handle_submit,
            shadow="lg",
            padding="1em",
            border_radius="lg",
            width="100%",
            ),
            pc.cond(State.is_working,
                pc.spinner(
                    color="lightgreen",
                    thickness=5,
                    speed="1.5s",
                    size="xl",
                ),),
        ),
         width="100%",
    )



# Add state and page to the app.
app = pc.App(state=State)
app.add_page(index)
app.compile()
