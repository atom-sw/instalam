# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import random
import pytest
from instalam.instalam import Candidate, Ballot, Election, read_ballots, TieBreakingRule

def test_add_preference():
    ballot = Ballot()
    candidate = Candidate(name="Alice")
    ballot.add_preference(candidate, 1.0)
    # pylint: disable=protected-access
    assert ballot._ranks[candidate] == 1.0

def test_cast():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, 2.0)
    ballot.add_preference(candidate3, 1.0)
    ballot.cast(candidates = None)
    assert ballot.preferences == [(candidate1, candidate3), (candidate2,)]

def test_cast_unranked():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, 2.0)
    ballot.cast(candidates = set([candidate1, candidate2, candidate3]))
    assert ballot.preferences == [(candidate1,), (candidate2,), (candidate3,)]

def test_cast_invalid_candidate():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, 2.0)
    ballot.add_preference(candidate3, 1.0)
    ballot.cast(candidates = set([candidate1, candidate2]))
    assert ballot.preferences == [(candidate1,), (candidate2,)]

def test_top_preference():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, 2.0)
    ballot.cast()
    assert ballot.top_preference() == (candidate1,)

def test_remove_preference():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, 2.0)
    ballot.add_preference(candidate3, 1.0)
    ballot.cast()
    ballot.remove_preference(candidate1)
    assert ballot.preferences == [(candidate3,), (candidate2,)]

def test_voted():
    ballot = Ballot()
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    ballot.add_preference(candidate1, 1.0)
    ballot.add_preference(candidate2, -2.0)
    ballot.cast()
    assert candidate1 in ballot.voted()
    assert candidate2 in ballot.voted()
    assert candidate3 not in ballot.voted()


def test_all_pebbles_all_votes():
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    ballot1 = Ballot()
    ballot1.add_preference(candidate1, 1.0)
    ballot1.add_preference(candidate2, 1.5)
    ballot1.cast()
    ballot2 = Ballot()
    ballot2.add_preference(candidate2, 1.0)
    ballot2.add_preference(candidate1, -1.5)
    ballot2.cast()
    election12 = Election(ballots=[ballot1, ballot2])
    assert election12.all_pebbles() == 1
    assert election12.all_votes() == 2
    ballot3 = Ballot()
    ballot3.add_preference(candidate1, 1.0)
    ballot3.add_preference(candidate2, 1.0)
    ballot3.cast()
    election13 = Election(ballots=[ballot1, ballot3])
    assert election13.all_pebbles() == 2
    assert election13.all_votes() == 4

def test_tally_standings():
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    ballot1 = Ballot()
    ballot1.add_preference(candidate1, 1.0)
    ballot2 = Ballot()
    ballot2.add_preference(candidate2, 1.0)
    election12 = Election(ballots=[ballot1, ballot2], candidates=set([candidate1, candidate2]))
    tally12 = election12.tally()
    standings12 = election12.standings()
    assert tally12[candidate1] == 1
    assert tally12[candidate2] == 1
    assert standings12[candidate1] == 50.0
    assert standings12[candidate2] == 50.0
    ballot3 = Ballot()
    ballot3.add_preference(candidate1, 1.0)
    ballot3.add_preference(candidate2, 1.0)
    ballot4 = Ballot()
    election34 = Election(ballots=[ballot3, ballot4], candidates=set([candidate1, candidate2]))
    tally34 = election34.tally()
    standings34 = election34.standings()
    assert tally34[candidate1] == 2
    assert tally34[candidate2] == 2
    assert standings34[candidate1] == 50.0
    assert standings34[candidate2] == 50.0
    ballot4 = Ballot()
    ballot4.add_preference(candidate1, 0.0)
    election14 = Election(ballots=[ballot1, ballot4], candidates=set([candidate1, candidate2]))
    tally14 = election14.tally()
    standings14 = election14.standings()
    assert tally14[candidate1] == 2
    assert tally14[candidate2] == 0
    assert standings14[candidate1] == 100.0
    assert standings14[candidate2] == 0.0

def test_top_candidates():
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    candidates = set([candidate1, candidate2, candidate3])
    ballot1 = Ballot()
    ballot1.add_preference(candidate1, 1.0)
    ballot1.add_preference(candidate2, 2.0)
    ballot1.add_preference(candidate3, 3.0)
    ballot1.cast(candidates)
    ballot2 = Ballot()
    ballot2.add_preference(candidate1, 1.0)
    ballot2.add_preference(candidate2, 1.0)
    ballot2.add_preference(candidate3, 3.0)
    ballot2.cast(candidates)
    ballot3 = Ballot()
    ballot3.add_preference(candidate3, 1.0)
    ballot3.cast(candidates)
    election12 = Election(ballots=[ballot1, ballot2], candidates=candidates)
    top_candidates12, votes12 = election12.top_candidates()
    assert top_candidates12 == set([candidate1])
    assert election12.is_majority(votes12)
    election123 = Election(ballots=[ballot1, ballot2, ballot3])
    top_candidates123, votes123 = election123.top_candidates()
    assert top_candidates123 == set([candidate1])
    assert not election123.is_majority(votes123)

def test_bottom_candidates():
    candidate1 = Candidate(name="Alice")
    candidate2 = Candidate(name="Bob")
    candidate3 = Candidate(name="Charlie")
    candidates = set([candidate1, candidate2, candidate3])
    ballot1 = Ballot()
    ballot1.add_preference(candidate1, 1.0)
    ballot1.add_preference(candidate2, 2.0)
    ballot1.add_preference(candidate3, 3.0)
    ballot1.cast(candidates)
    ballot2 = Ballot()
    ballot2.add_preference(candidate1, 1.0)
    ballot2.add_preference(candidate2, 1.0)
    ballot2.add_preference(candidate3, 3.0)
    ballot2.cast(candidates)
    ballot3 = Ballot()
    ballot3.add_preference(candidate3, 1.0)
    ballot3.cast(candidates)
    election123 = Election(ballots=[ballot1, ballot2, ballot3])
    bottom_candidates123, _ = election123.bottom_candidates()
    assert bottom_candidates123 == set([candidate2])
    ballot4 = Ballot()
    ballot4.add_preference(candidate1, 1.0)
    ballot4.add_preference(candidate2, 2.0)
    ballot4.cast()
    ballot5 = Ballot()
    ballot5.add_preference(candidate2, 1.0)
    ballot5.add_preference(candidate1, 2.0)
    ballot5.cast()
    election45 = Election(ballots=[ballot4, ballot5])
    bottom_candidates45, _ = election45.bottom_candidates()
    assert bottom_candidates45 == set([candidate1, candidate2])

def test_module_example():
    # There are two candidates in this election
    alice = Candidate(name="Alice")
    bob = Candidate(name="Bob")
    candidates = {alice, bob}
    # The first voter ranks Alice first and Bob second
    ballot1 = Ballot()
    ballot1.add_preference(alice, 1)
    ballot1.add_preference(bob, 2)
    ballot1.cast(candidates)
    # The second voter does not express any preference,
    # which is equivalent to ranking all candidates equally
    ballot2 = Ballot()
    ballot2.cast(candidates)
    # Let's run an election with these ballots
    election = Election(ballots={ballot1, ballot2}, candidates=candidates)
    outcome = election.instant_runoff()
    # The winner of the election is Alice
    assert outcome == { alice }

def tennessee_election():
    # Simulating the example from https://electowiki.org/wiki/Instant-runoff_voting
    # pylint: disable=invalid-name
    C = Candidate(name="Chattanooga")
    K = Candidate(name="Knoxville")
    M = Candidate(name="Memphis")
    N = Candidate(name="Nashville")
    candidates = set([C, K, M, N])
    ballots = []
    for _ in range(42):
        ballot = Ballot()
        ballot.add_preference(M, 1.0)
        ballot.add_preference(N, 2.0)
        ballot.add_preference(C, 3.0)
        ballot.add_preference(K, 4.0)
        ballots.append(ballot)
    for _ in range(26):
        ballot = Ballot()
        ballot.add_preference(N, 1.0)
        ballot.add_preference(C, 2.0)
        ballot.add_preference(K, 3.0)
        ballot.add_preference(M, 4.0)
        ballots.append(ballot)
    for _ in range(15):
        ballot = Ballot()
        ballot.add_preference(C, 1.0)
        ballot.add_preference(K, 2.0)
        ballot.add_preference(M, 3.0)
        ballot.add_preference(N, 4.0)
        ballots.append(ballot)
    for _ in range(17):
        ballot = Ballot()
        ballot.add_preference(K, 1.0)
        ballot.add_preference(C, 2.0)
        ballot.add_preference(N, 3.0)
        ballot.add_preference(M, 4.0)
        ballots.append(ballot)
    election = Election(ballots=ballots, candidates=candidates)
    return (election, C, K, M, N)

def test_election():
    # pylint: disable=invalid-name
    election, C, K, M, N = tennessee_election()
    most_voted, most_votes = election.top_candidates()
    print(election.standings())
    assert most_voted == set([M])
    assert not election.is_majority(most_votes)
    least_voted, _ = election.bottom_candidates()
    assert least_voted == set([C])
    election.eliminate(least_voted)
    print(election.standings())
    most_voted, most_votes = election.top_candidates()
    assert most_voted == set([M])
    assert not election.is_majority(most_votes)
    least_voted, _ = election.bottom_candidates()
    assert least_voted == set([N])
    election.eliminate(least_voted)
    print(election.standings())
    most_voted, most_votes = election.top_candidates()
    assert most_voted == set([K])
    assert election.is_majority(most_votes)

def test_instant_runoff():
    election, _, _, _, _ = tennessee_election()
    election.instant_runoff()
    assert election.round == 3


def test_read_ballots():
    ballots, candidates = read_ballots("tests/Simpsons_ranked_voting.xlsx")
    assert len(ballots) == 3
    assert len(candidates) == 10
    election = Election(ballots=ballots, candidates=candidates)
    outcome = election.instant_runoff(ties=TieBreakingRule.ALL)
    assert len(outcome) == 1
    assert Candidate("Marge Simpson") in outcome


def random_candidates(n_candidates: int) -> set[Candidate]:
    return {Candidate(name=f"Candidate {i}") for i in range(n_candidates)}

def random_ballot(candidates: set[Candidate], prob: float = 0.05) -> Ballot:
    ballot = Ballot()
    for candidate in candidates:
        # Randomly skip some candidates
        if random.random() < prob:
            continue
        rank = random.randint(0, len(candidates))
        ballot.add_preference(candidate, rank)
    ballot.cast(candidates)
    return ballot

def random_election(n_candidates: int, n_voters: int) -> Election:
    candidates = random_candidates(n_candidates)
    ballots = [random_ballot(candidates) for _ in range(n_voters)]
    return Election(ballots=ballots, candidates=candidates)

def test_random_election(capsys):
    for _ in range(100):
        election = random_election(10, 100)
        outcome = election.instant_runoff()
        assert len(outcome) > 0
    # Capture output for this test
    _ = capsys.readouterr()


if __name__ == "__main__":
    # -s: do not capture output (print it instead)
    pytest.main(["-s"])
