# Contributing guidelines

We thank you in advance :thumbsup: :tada: for taking the time to contribute, whether with *code* or with *ideas*, to the Local EGA project.


## Did you find a bug?

* Ensure that the bug was not already reported by [searching under Issues].

* If you're unable to find an (open) issue addressing the problem, [open a new one]. Be sure to prefix the issue title with **[BUG]** and to include:

  - a *clear* description,
  - as much relevant information as possible, and
  - a *code sample* or an (executable) *test case* demonstrating the expected behaviour that is not occurring.

* If possible, use the following [template to report a bug].

When you create a new issue, or work on an already existing one, assign yourself to that issue, and note that discussions on how to proceed about that issue do take place in the comment section on that issue.

## How we work with Git

All work take place in feature branches. Give your branch a short descriptive name and potentially, prefix the name with the most suitable of:

   * `feature/`
   * `docs/`
   * `bugfix/`
   * `test/`
   * `refactor/`

Use comments in your code, choose variable and function names that clearly show what you intend to implement.

Once the feature is done you can request it to be merged back into `master` by making a Pull Request.

Before making the pull request it is a good idea to rebase your branch to `master` to ensure that eventual conflicts with the `master` branch is solved before the PR is reviewed and we can therefore have a clean merge.


### About git and commit messages

In general, it is better to commit often. Small commits are easier to roll back and also makes the code easier to review.

Write helpful commit messages that describes the changes and possibly why they were necessary.

Each commit should contain changes that are functionally connected and/or related.

Learn how to select chunks of changed files to do multiple separate commits of unrelated things. This can be done with either `git add -p` or `git commit -p`.

Refer to [how to Write a Git Commit Message](http://chris.beams.io/posts/git-commit/).


### How we do code reviews

A code review is initiated when someone has made a Pull Request in the appropriate repository on github.

Work should not continue on the branch _unless_ it is a [Draft Pull Request](https://github.blog/2019-02-14-introducing-draft-pull-requests/). Once the PR is marked ready the review can start.

The initiator of the PR recruits 2 reviewers and assign them on the PR.

A reviewers job is to:

  * Write polite and friendly comments - remember that it can be tough to have other people critizising your work, a little kindness goes a long way. This does not mean we should not comment on things that need to be changed of course.
  * Read the code and make sure it is understandable
  * Make sure that commit messages and commits are structured so that it is possible to understand why certain changes were made.
  * Ensure that the testsuite covers the new behavior

Once all the reviews are positive the Pull Request can be _merged_ and the feature branch deleted.


----

Thanks again,  
/CRG System Developers

[searching under Issues]: https://github.com/EGA-archive/LocalEGA/issues?utf8=%E2%9C%93&q=is%3Aissue%20label%3Abug%20%5BBUG%5D%20in%3Atitle
[open a new one]: https://github.com/EGA-archive/LocalEGA/issues/new?title=%5BBUG%5D
[template to report a bug]: https://github.com/EGA-archive/LocalEGA/issues/new?template=bug-report.md
