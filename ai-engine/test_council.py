# tests for the council these use fake models so they dont need api keys
# run with pytest -v

from council import count_votes, read_vote, run_council


# a pretend llm that always gives the same reply
class FakeModel:
    def __init__(self, reply):
        self.reply = reply

    def call(self, question):
        return self.reply


# a pretend llm that breaks like when an api key is wrong
class BrokenModel:
    def call(self, question):
        raise ValueError("invalid api key")


def vote(v):
    return {"model": "fake", "vote": v, "reply": ""}


# reading the votes

def test_reads_the_vote_from_the_first_line():
    assert read_vote("DECLINE\nthe stress test failed") == "DECLINE"


def test_reads_lowercase_and_extra_words():
    assert read_vote("my vote: refer\nneeds a valuation") == "REFER"


def test_no_vote_gives_none():
    assert read_vote("I am not sure") is None


# counting the votes

def test_majority_wins():
    assert count_votes([vote("DECLINE"), vote("DECLINE"), vote("APPROVE")], "APPROVE")[0] == "DECLINE"


def test_all_disagree_gives_refer():
    assert count_votes([vote("DECLINE"), vote("REFER"), vote("APPROVE")], "APPROVE")[0] == "REFER"


def test_one_model_failed_still_works():
    assert count_votes([vote("APPROVE"), vote("APPROVE"), vote(None)], "DECLINE")[0] == "APPROVE"


def test_two_models_failed_uses_the_rules():
    assert count_votes([vote("APPROVE"), vote(None), vote(None)], "DECLINE")[0] == "DECLINE"


# the whole council with fake models

def test_council_with_a_broken_model():
    models = {"a": FakeModel("DECLINE\nfailed stress test"),
              "b": FakeModel("DECLINE\ntoo risky"),
              "c": BrokenModel()}
    result = run_council({}, {}, "APPROVE", models)
    assert result["decision"] == "DECLINE"
    assert result["votes"][2]["reply"] == "failed: invalid api key"