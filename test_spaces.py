from nodes import llm

text = llm.invoke("Write one sentence about abacus beads in schools.").content
print(repr(text))
print([hex(ord(c)) for c in text if ord(c) > 127])