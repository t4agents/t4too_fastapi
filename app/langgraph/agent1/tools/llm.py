from langchain_openai import ChatOpenAI

def llm(input):
    model = ChatOpenAI(model='gpt-5-nano') # Initialize an LLM
    output = model.invoke(input)
    return output.content # Return just the text content

def token_counter(input):
    tokens = str(input).split() # Split the text into words
    count_no = len(tokens)
    return count_no