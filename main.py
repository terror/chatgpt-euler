import json
import os
import re
import subprocess
import time
import typing as t
from dataclasses import dataclass

from dotenv import load_dotenv
from revChatGPT.revChatGPT import Chatbot

POSTFIX = '''
First, give a single numerical answer to the problem without using any commas.
Then, below the numerical answer to the problem, explain in detail how
you came up with that answer. Make sure to format all of your mathematical
expressions using valid LaTeX code.
'''

@dataclass
class Env:
  session_token: t.Union[str, None]

  @staticmethod
  def load():
    load_dotenv()
    return Env(os.getenv('SESSION_TOKEN'))

  def as_dict(self):
    return {'Authorization': '', 'session_token': self.session_token}

class Bot:
  def __init__(self, client):
    self.client = client

  def refresh(self):
    self.client.refresh_session()
    self.client.reset_chat()

  def query(self, message):
    return self.client.get_chat_response(message)['message']

def main(bot):
  bot.refresh()

  with open('problems.json') as problem_file:
    problems = json.load(problem_file)

  with open('answers.json') as answer_file:
    answers = json.load(answer_file)

  correct, handle = 0, open('results.md', 'a')

  for problem, text in problems.items():
    print(f'Fetching answer to problem {problem}...')

    found = 0

    while not found:
      try:
        result = bot.query(text + '\n' + POSTFIX)
      except:
        continue
      found = 1

    is_correct = answers[problem] == re.findall(
      r"[-+]?(?:\d*\.*\d+)", result.split('\n')[0]
    )[-1]

    correct += is_correct

    output = f'## Problem {problem} {"✅" if is_correct else "❌"}\n> {text}\n\n{result}\n'

    print(output)
    handle.write(output)

    time.sleep(2)

  handle.close()

  print(f'Number of correct answers: {correct}')
  print(f'Number of incorrect answers: {len(problems) - correct}')

if __name__ == '__main__':
  main(Bot(Chatbot(Env.load().as_dict())))
