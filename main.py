import json
import os
import re
import subprocess
import sys
import time
import traceback
import typing as t
from argparse import ArgumentParser
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
class Arguments:
  problem: t.Union[str, None]
  start: t.Union[str, None]
  verbose: bool

  @staticmethod
  def from_args():
    parser = ArgumentParser()

    parser.add_argument(
      '-p',
      '--problem',
      required=False,
      type=str,
      help='Specific problem to run'
    )

    parser.add_argument(
      '-s', '--start', required=False, type=str, help='Starting problem'
    )

    parser.add_argument(
      '-v', '--verbose', required=False, type=bool, help='Print out tracebacks'
    )

    return Arguments(**vars(parser.parse_args()))

  def run(self):
    Runner(self).run()

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

class Runner:
  def __init__(self, args):
    self.args = args

    self.bot = Bot(Chatbot(Env.load().as_dict()))

    with open('problems.json') as problem_file:
      self.problems = json.load(problem_file)

    with open('answers.json') as answer_file:
      self.answers = json.load(answer_file)

  def run(self):
    correct, handle = 0, open('results.md', 'a')

    if self.args.problem:
      output, _ = self.__problem(self.args.problem, self.problems[self.args.problem])
      print(output)
      handle.write(output)
    else:
      correct = self.__iterate(self.args.start)
      print(f'Number of correct answers: {correct}')
      print(
        f'Number of incorrect answers: {len(self.problems) - self.args.start - correct}'
      )

    handle.close()

  def __iterate(self, start):
    correct, handle = 0, open('results.md', 'a')

    for problem in list(self.problems.keys())[max(0, start - 1):]:
      text = self.problems[problem]
      output, is_correct = self.__problem(problem, text)
      correct += is_correct
      print(output)
      handle.write(output)
      time.sleep(2)

    handle.close()

    return correct

  def __problem(self, number, text):
    self.bot.refresh()

    print(f'Fetching answer to problem {number}...')

    found = 0

    while not found:
      try:
        result = self.bot.query(text + POSTFIX)
      except:
        continue
      found = 1

    numbers = re.findall(r"[-+]?(?:\d*\.*\d+)", result.split('\n')[0])

    is_correct = numbers and self.answers[number] == numbers[-1]

    return (
      f'## Problem {number} {"✅" if is_correct else "❌"}\n> {text}\n\n{result}\n',
      is_correct
    )

def err(*args, **kwargs):
  print(*args, **kwargs, file=sys.stderr)
  sys.exit(1)

def main(args):
  try:
    args.run()
  except Exception as error:
    if args.verbose:
      traceback.print_exc()
    err(f'error: {error}')

if __name__ == '__main__':
  main(Arguments.from_args())
