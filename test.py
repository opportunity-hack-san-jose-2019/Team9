from schedule import scheduleInterviewes
from flask import Flask

application = Flask(__name__)


if __name__ == "__main__":
  application.run(debug=True)
