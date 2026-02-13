from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_and_split(path: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_text(text)
