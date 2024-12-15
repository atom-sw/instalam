"""
instalam.py

This module provides a simple implementation of ranked voting elections.

Classes:
    Candidate: Represents a candidate in an election.
    Ballot: Represents a ballot in an election, containing ranked preferences for all candidates.
    Election: Represents an election with a set of ballots and candidates.

Functions:
    read_ballots: Reads ballots from an Excel file and returns a list of Ballot objects.

Usage:
    This module can be used to create candidates, ballots, and determine the outcome of
    an election using ranked voting systems.

    Example usage:

        # There are two candidates in this election
        candidate1 = Candidate(name="Alice")
        candidate2 = Candidate(name="Bob")
        candidates = {candidate1, candidate2}
        # The first voter ranks Alice first and Bob second
        ballot1 = Ballot()
        ballot1.add_preference(candidate1, 1)
        ballot1.add_preference(candidate2, 2)
        ballot1.cast(candidates)
        # The second voter does not express any preference,
        # which is equivalent to ranking all candidates equally
        ballot2 = Ballot()
        ballot2.cast(candidates)
        # Let's run an election with these ballots
        election = Election(ballots={ballot1, ballot2}, candidates=candidates)
        outcome = election.instant_runoff()
        # The winner of the election is Alice
        print(outcome)
"""
import argparse
from dataclasses import dataclass
from functools import reduce
import math
import enum
import random
import pandas


@dataclass(frozen=True, eq=True)
class Candidate:
    """
    A candidate in an election.

    Attributes:
        name (str): The name of the candidate.
    """
    name: str

    def __str__(self):
        return self.name


class Ballot:
    """
    A ballot in an election, containing ranked preferences for
    candidates.

    Attributes:
        preferences (list[tuple[Candidate]]): A list of tuples
          representing the ranked preferences of candidates.

        _ranks (dict[Candidate, float]): A dictionary mapping
          candidates to their assigned ranks.

    Methods:
        __init__(): Initializes a new Ballot instance with empty
          preferences and ranks.

        add_preference(candidate: Candidate, rank: float): Adds a
          candidate with a specified rank to the ballot.

        cast(candidates: set[Candidate] = None): Finalizes the ballot
          by sorting and grouping candidates by their ranks.

        top_preference() -> tuple[Candidate]: Returns the top
          preference or preferences from the ballot.

        remove_preference(candidate: Candidate): Removes a specified
          candidate from the ballot preferences.
    """
    preferences: list[tuple[Candidate]]
    _ranks: dict[Candidate, float]

    def __init__(self):
        """
        Initializes a new Ballot instance with empty preferences
        and ranks.
        """
        self.preferences = []
        self._ranks = {}

    def __str__(self):
        """
        Returns a string representation of the ballot.

        Returns:
            str: A string describing the ballot preferences.
        """
        res = "\n".join([f"{index + 1}. {', '.join([str(c) for c in candidate])}"
                         for index, candidate in enumerate(self.preferences)])
        return res

    def add_preference(self, candidate: Candidate, rank: float):
        """
        Adds a candidate with a specified rank to the ballot.

        Args:
            candidate (Candidate): The candidate to add.

            rank (float): The rank to assign to the candidate. The
              value of the rank is only used as an ordering criterion, its
              absolute value does not matter.
        """
        self._ranks[candidate] = rank

    def cast(self, candidates: set[Candidate] = None):
        """
        Finalizes the ballot by sorting and grouping candidates by
        their ranks.

        Args:

           candidates (set[Candidate], optional): A set of candidates to
             consider. If provided, only these candidates will be included
             in the final preferences, and any of these candidates without a
             rank will be ranked last.
        """
        preferences = sorted(self._ranks.items(), key=lambda item: item[1])
        self.preferences = []
        k, cur_rank, cur_candidates = 0, None, []
        while k < len(preferences):
            candidate, rank = preferences[k]
            if cur_rank is None or rank == cur_rank:
                cur_rank = rank
                cur_candidates.append(candidate)
            else:
                self.preferences.append(tuple(cur_candidates))
                cur_rank, cur_candidates = rank, [candidate]
            k += 1
        if cur_candidates:
            self.preferences.append(tuple(cur_candidates))
        if candidates is not None:
            ranked = { c for p in self.preferences for c in p }
            # Remove all candidates not in `candidates`
            for removed_candidate in ranked - candidates:
                self.remove_preference(removed_candidate)
            # Add all candidates not explicitly ranked in last position
            last = tuple(c for c in candidates if c not in ranked)
            if last:
                self.preferences.append(last)

    def top_preference(self) -> tuple[Candidate]:
        """
        Returns the top preference from the ballot.

        Returns:
            tuple[Candidate]: The top preference, or preferences, from the ballot.
        """
        return self.preferences[0]

    def remove_preference(self, candidate: Candidate):
        """
        Removes a specified candidate from the ballot preferences.

        Args:
            candidate (Candidate): The candidate to remove.
        """
        self.preferences = [tuple(c for c in p if c != candidate)
                            for p in self.preferences]
        self.preferences = [p for p in self.preferences if p]

    def voted(self) -> list[Candidate]:
        """
        Returns the candidates that have been voted in the ballot.

        Returns:
            list[Candidate]: The candidates that have been voted in the ballot.
        """
        return [c for p in self.preferences for c in p]


@enum.unique
class TieBreakingRule(enum.Enum):
    """
    Enum representing the rules for breaking ties in an election.
    Based on https://electowiki.org/wiki/Instant-runoff_voting#Handling_ties_in_IRV_elections

    Attributes:
        ALL (str): Eliminate all tied candidates at once.
        RANDOM (str): Eliminate one tied candidate at random.
        RVH (str): Random voter hierarchy method: determine a strict ordering
          of the candidates and use it to eliminate candidates.
    """
    ALL = "eliminate all tied candidates at once"
    RANDOM = "eliminate one tied candidate at random"
    RVH = ("random voter hierarchy (randomly determine a strict ordering of the candidates,"
           " use it to eliminate candidates)")


class Election:
    """Represents an election with a set of ballots and candidates.

    Attributes:
        ballots (set[Ballot]): A set of ballots in the election.

        candidates (set[Candidate]): A set of candidates in the election.

        round (int): The current round of the election.

        _rvh (list[Candidate]): The candidates listed in a random order.

    Methods:
      __init__(ballots: set[Ballot], candidates: set[Candidate] = None):
        Initializes a new Election instance.

      __str__(): Returns a string representation of the election.

      all_votes() -> int: Returns the total number of votes (in
        pebbles units) in the election.

      all_pebbles() -> int: Returns the least common multiple of the
        number of tied top preferences.

      tally(as_sorted: bool = True) -> dict[Candidate, int]: Returns a
        tally of votes for each candidate.

      standings() -> dict[Candidate, float]: Returns the tally of
        votes as percentages of the total votes for top preferences.

      is_majority(votes: int) -> bool: Does the number of votes (in
        pebble units) constitute an absolute majority?

      top_candidates() -> tuple[set[Candidate], int]: Returns the
        candidates tied for top preferences, and the number of votes
        (in pebble units) they received.

      bottom_candidates() -> tuple[set[Candidate], int]: Returns the
        candidates tied for least preferences, and the number of votes
        (in pebble units) they received.

      to_eliminate(set[Candidate], TieBreakingRule) -> set[Candidate]:
        Returns a subset of the given set of candidates that should be
        eliminated according to the given tie-breaking rule.

      eliminate(set[Candidate]): Removes the given candidates from all
        the ballots.

      instant_runoff(TieBreakingRule): Runs an election with instant
        runoff, printing progress incrementally.

    """

    ballots: set[Ballot]
    candidates: set[Candidate]
    round: int
    _rvh: list[Candidate]

    def __init__(self, ballots: set[Ballot], candidates: set[Candidate] = None):
        """
        Initializes a new Election instance.

        Args:
            ballots (set[Ballot]): A set of ballots in the election.

            candidates (set[Candidate], optional): A set of candidates
              in the election. If not provided, it will be derived from the
              ballots.
        """
        self.ballots = ballots
        if candidates is None:
            self.candidates = { c for b in ballots for c in b.voted() }
        else:
            self.candidates = candidates
            for ballot in ballots:
                ballot.cast(candidates=candidates)
        self.round = 0
        self._rvh = list(self.candidates)
        random.shuffle(self._rvh)

    def __str__(self):
        """
        Returns a string representation of the election.

        Returns:
            str: A string describing the current round, number of
              ballots, and number of candidates.
        """
        res = (f"Round #{self.round} of election with {len(self.ballots)} ballots"
               f" and {len(self.candidates)} candidates")
        return res

    def all_votes(self) -> int:
        """
        Returns the total number of votes (in pebble units) in the election.

        Returns:
            int: The total number of votes.
        """
        return len(self.ballots) * self.all_pebbles()

    def all_pebbles(self) -> int:
        """
        Returns the least common multiple of the number of tied
        top preferences.

        Returns:
            int: The least common multiple of the number of tied top
            preferences.

        """
        prefs = [len(b.top_preference()) for b in self.ballots]
        return reduce(lambda x, y: x * y // math.gcd(x, y), prefs)

    def tally(self, as_sorted: bool = True) -> dict[Candidate, int]:
        """
        Returns a tally of votes for each candidate.

        Args:
            as_sorted (bool, optional): If True, returns the tally sorted by

        Returns:
            dict[Candidate, int]: A dictionary mapping candidates to
              their top-preference votes (in pebble units).
        """
        counts = {c: 0 for c in self.candidates}
        pebbles = self.all_pebbles()
        for ballot in self.ballots:
            # If ties, add fractional vote
            top = ballot.top_preference()
            for candidate in top:
                assert pebbles % len(top) == 0
                counts[candidate] += pebbles // len(top)
        if as_sorted:
            return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
        return counts

    def standings(self) -> dict[Candidate, float]:
        """
        Returns the tally of votes as percentages of the total votes
        for top preferences.

        Returns:
          dict[Candidate, float]: A dictionary mapping candidates to
            their percentage of top preferences.

        """
        total_votes = self.all_votes()
        tally = self.tally()
        return {c: (v / total_votes) * 100 for c, v in tally.items()}

    def is_majority(self, votes: int) -> bool:
        """
        Does the number of votes (in pebble units) constitute an
        absolute majority?

        Args:
            votes (int): The number of votes to check.

        Returns:
            bool: True if the votes constitute a majority, False
              otherwise.

        """
        return votes > self.all_votes() / 2

    def top_candidates(self) -> tuple[set[Candidate], int]:
        """
        Returns the candidates tied for top preferences, and the
        number of votes (in pebble units) they received.

        Returns:
            tuple[set[Candidate], int]: A tuple containing a set
              of the top candidates and the number of votes they
              received.
        """
        votes = self.tally(as_sorted=True)
        most_votes = list(votes.values())[0]
        most_voted = [c for c, v in votes.items() if v == most_votes]
        return (set(most_voted), most_votes)

    def bottom_candidates(self) -> tuple[set[Candidate], int]:
        """
        Returns the candidates tied for least preferences, and the number of
        votes (in pebble units) they received.

        Returns:
            tuple[set[Candidate], int]: A tuple containing a set
              of the bottom candidates and the number of votes they
              received.
        """
        votes = self.tally(as_sorted=True)
        least_votes = list(votes.values())[-1]
        least_voted = [c for c, v in votes.items() if v == least_votes]
        return (set(least_voted), least_votes)

    def to_eliminate(self, candidates: set[Candidate],
                     ties: TieBreakingRule = TieBreakingRule.ALL) -> set[Candidate]:
        """
        Returns a subset of the given set of candidates that should be
        eliminated according to the given tie-breaking rule.

        Args:
            candidates (set[Candidate]): The set of candidates to consider for elimination.

            ties (TieBreakingRule, optional): The tie-breaking rule to
              use. Defaults to TieBreakingRule.ALL.

        Returns:
            set[Candidate]: The set of candidates to eliminate.
        """
        if len(candidates) == 1:
            return candidates
        if ties == TieBreakingRule.ALL:
            return candidates
        if ties == TieBreakingRule.RANDOM:
            return { random.choice(list(candidates)) }
        if ties == TieBreakingRule.RVH:
            rvh = [c for c in self._rvh if c in candidates]
            assert len(rvh) > 0
            return { rvh[0] }
        raise ValueError(f"Invalid tie-breaking rule: {ties}")

    def eliminate(self, candidates: set[Candidate]):
        """
        Removes the given candidates from all the ballots.

        Args:
            candidates (set[Candidate]): The set of candidates to eliminate.
        """
        self.candidates -= candidates
        for ballot in self.ballots:
            for candidate in candidates:
                ballot.remove_preference(candidate)

    def instant_runoff(self, ties: TieBreakingRule = TieBreakingRule.ALL) -> set[Candidate]:
        """
        Runs an election with instant runoff, printing progress incrementally.

        Args:
            ties (TieBreakingRule, optional): The tie-breaking rule to
              use. Defaults to TieBreakingRule.ALL.

        Returns:
            set[Candidate]: The set of candidates that won the election.
        """
        self.round = 1
        while True:
            if self.round > 1:
                print("")
            print("-------------------------------------")
            print(str(self) + "\n")
            votes = self.standings()
            for candidate, votes in votes.items():
                print(f"{candidate.name}: {votes}%")
            most_voted, most_votes = self.top_candidates()
            if self.is_majority(most_votes):
                print(f"\nMajority winner{'' if len(most_voted) == 1 else 's (tied)'}: " +
                      ', '.join([str(c) for c in most_voted]))
                return most_voted
            print("\nThe top-preference candidate"
                  f"{'s do' if len(most_voted) > 1 else ' does'} not have absolute majority.")
            least_voted, _ = self.bottom_candidates()
            print(f"\n{'Tied candidates' if len(least_voted) > 1 else 'Candidate'} "
                  f"with the least preferences: {', '.join([str(c) for c in least_voted])}")
            to_eliminate = self.to_eliminate(least_voted, ties)
            if to_eliminate == self.candidates:
                print("\nAll remaining candidates are tied: "
                      f"{', '.join([str(c) for c in to_eliminate])}")
                return to_eliminate
            print("\nEliminating candidate" + ("s" if len(to_eliminate) > 1 else "") +
                  " with the least preferences: "
                  f"{', '.join([str(c) for c in to_eliminate])}")
            self.eliminate(to_eliminate)
            self.round += 1


def read_ballots(filename: str, first_column_idx: int = 1) -> tuple[list[Ballot], set[Candidate]]:
    """
    Reads ballots from an Excel file and returns a list of Ballot objects. The Excel file
    can be easily generated from an online form such as Google Forms or similar survey tool.

    Args:
        filename (str): The path to the Excel file containing the ballots.

        first_column_idx (int, optional): The (0-based) index of the first column
          containing candidate rankings. Defaults to 1 (i.e., the second column).

    Returns a tuple containing:
        list[Ballot]: A list of Ballot objects created from the data in the Excel file.
        set[Candidate]: A set of candidates in the election.
    """
    data_frame = pandas.read_excel(filename)
    data = data_frame.iloc[:, first_column_idx:]
    ballots = []
    candidates = set()
    for _, row in data.iterrows():
        ballot = Ballot()
        for name, value in row.items():
            candidate = Candidate(name)
            candidates |= { candidate }
            if pandas.notna(value):
                ballot.add_preference(candidate, value)
        ballot.cast(candidates)
        ballots.append(ballot)
    return (ballots, candidates)


def main():
    # pylint: disable=missing-function-docstring
    parser = argparse.ArgumentParser(description="Read ballots from an Excel file "
                                     "and runs an instant-runoff election.")
    parser.add_argument("filename", type=str, help="Path to the Excel file containing the ballots.")
    parser.add_argument("-f", "--first-column-index", type=int, default=1,
                        help="The 0-based index of the first column containing candidate rankings. "
                        "Defaults to 1 (i.e., second column).")
    parser.add_argument("-t", "--tie-breaking-rule",
                        choices=[rule.name for rule in TieBreakingRule],
                        default="ALL", help="The rule to use for breaking ties. Defaults to ALL.")
    args = parser.parse_args()
    ballots, candidates = read_ballots(args.filename, args.first_column_index)
    print(f"Read {len(ballots)} ballots and {len(candidates)} candidates from {args.filename}.")
    print("Candidates: " + ", ".join(sorted([str(c) for c in candidates])))
    input("\nPress Enter to run the instant-runoff election.\n")
    election = Election(ballots=ballots, candidates=candidates)
    tie_breaking = [rule for rule in TieBreakingRule if rule.name == args.tie_breaking_rule]
    assert len(tie_breaking) == 1
    election.instant_runoff(ties=tie_breaking[0])


if __name__ == "__main__":
    main()
