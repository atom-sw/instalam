# Insta-Lam

A simple implementation of ranked voting elections using the instant runoff method, based on the [description on the Electo wiki](https://electowiki.org/wiki/Instant-runoff_voting).


## Installation

You can install this package directly from GitHub:

```sh
pip install git+https://github.com/atom-sw/instalam
```


## Usage


### From the command line

As a command-line tool, you can use `instalam` to import votes from a spreadsheet organized as follows:
See <tests/Simpsons_ranked_voting.xlsx> for an example.

| Metadata | Candidate 1 | Candidate 2 | Candidate 3 | ... |
|----------|-------------|-------------|-------------|-----|
| ballot 1 | rank 1, 1   | rank 1, 2   | rank 1, 3   | ... |
| ballot 2 | rank 2, 1   | rank 2, 2   | rank 2, 3   | ... |
| ballot 3 | rank 3, 1   | rank 3, 2   | rank 3, 3   | ... |
| ...      | ...         | ...         | ...         | ... |

- Each row, except the first row, which is a header, is a ballot.
- The first column is metadata, which is ignored.
- The other columns represent the ranks given to each candidate.

The ranks can be any number. What matters for the ranking is the relative order of ranks within each ballot. For example, if `rank k, c < rank k, d`, it means that candidate `c` is preferred over candidate `d` in ballot `k`. Two candidates are tied if they have the same rank. If there is no rank in a ballot for some candidate `c`, then that candidate will be ranked last (possibly tied with other candidates without an explicit rank).

Here is how you import ballots from such a spreadsheet, and run an instant runoff vote with them:

```sh
instalam spreadsheet.xlsx
```

If you have `N` columns of metadata in the spreadsheet before the candidates' ranks,
then pass option `-f N` to `instalam`. By default `N` is `1`, which corresponds to a single metadata column.

There is another option `-t` to specify the [tie-breaking method](https://electowiki.org/wiki/Instant-runoff_voting#Handling_ties_in_IRV_elections). Try `instalam -h` for details.


### Programmatically

Here is a simple example of instant runoff voting with `instalam` used as a library.

```python
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
print(f"The winner is: {outcome}")
```


## Testing

If you want to run the tests, install the project in edit mode first:

```sh
# From the project's root
pip install -e .
# Run all tests in tests/
pytest tests/
```
