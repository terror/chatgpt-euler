import asyncio
import os
import subprocess
import time
import typing as t
from dataclasses import dataclass

from dotenv import load_dotenv
from revChatGPT.revChatGPT import Chatbot

POSTFIX = '''
First enter a single numerical answer without any
other words to go along with the answer, and then
explain how you came up with that single numerical answer.

Format your mathematical expression using LaTeX.
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

@dataclass
class Report:
  is_error: bool
  stdout: str

class Subprocess:
  def __init__(self, base):
    self.base = base

  def run(self, args):
    return (
      lambda result: Report(result.returncode != 0, result.stdout.decode())
    )(subprocess.run([self.base] + args.split(), stdout=subprocess.PIPE))

def main(bot, proc):
  bot.refresh()

  problem = 1

  while True:
    result = proc.run(f'--preview {problem}')

    if result.is_error:
      break

    try:
      result = bot.query(
        '\n'.join(result.stdout.split('\n')[1:]) + POSTFIX + '\n'
      )
    except:
      continue

    print(f'## Problem {problem}\n{result}')

    problem += 1
    time.sleep(5)

if __name__ == '__main__':
  main(Bot(Chatbot(Env.load().as_dict())), Subprocess('euler'))
