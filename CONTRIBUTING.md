# Contributing guidelines

We thank you in advance :thumbsup: :tada: for taking the time to
contribute, whether with *code* or with *ideas*, to the Local EGA
project.


## Highlevel overview of how we work

### Github projects
We use github projects in the EGA-Archive to manage our work

### How we use issues
 Issues are the central area for all work.

### Standups
 Every day at 10:30 we have standups in Zoom meeting: <id>

### Sprint Reviews and Planning
Approximately every 2 weeks we have sprint reviews and then also a sprint
planning meeting.

## Procedure


1. Create an issue on Github, and talk to the team members on the NBIS
   local-ega Slack channel. You can alternatively pick one already
   created.


2. Assign yourself to that issue.

#. Discussions on how to proceed about that issue take place in the
   comment section on that issue, beforehand.  
   
   The keyword here is *beforehand*. It is usually a good idea to talk
   about it first. Somebody might have already some pieces in place,
   we avoid unnecessary work duplication and a waste of time and
   effort.

#. Work on it (on a fork, or on a separate branch) as you wish. That's
   what `git` is good for. This GitHub repository follows
   the [coding guidelines from NBIS].
   
   Name your branch as you wish and prefix the name with:

   * `feature/` if it is a code feature
   * `hotfix/` if you are fixing an urgent bug

   Use comments in your code, choose variable and function names that
   clearly show what you intend to implement.

   Use [git rebase -i] in
   order to rewrite your history, and have meaningful commits.  That
   way, we avoid the _'Typo'_, _'Work In Progress (WIP)'_, or
   _'Oops...forgot this or that'_ commits.

   Limit the first line of your git commits to 72 characters or less.


#. Create a Pull Request (PR), so that your code is reviewed by the
   admins on this repository.  
   
   That PR should be connected to the issue you are working on.
   Moreover, the PR:
   
   - should use `Estimate=1`,
   - should be connected to:

     * an `Epic`,
     * a `Milestone` and
     * a `User story`
     * ... or several.

   N.B: Pull requests are done to the `dev` branch. PRs to `master` are rejected.

#. Selecting a review goes as follows: Pick one *main* reviewer.  It
   is usually one that you had discussions with, and is somehow 
   connected to that issue. If this is not the case, pick several reviewers.
   
   Note that, in turn, the main reviewer might ask another reviewer
   for help. The approval of all reviewers is compulsory in order to
   merge the PR. Moreover, the main reviewer is the one merging the
   PR, not you.
   
   Find more information on the [NBIS reviewing guidelines],


#. It is possible that your PR requires changes (because it creates
   conflicts, doesn't pass the integrated tests or because some parts
   should be rewritten in a cleaner manner, or because it does not
   follow the standards, or you're requesting the wrong branch to pull
   your code, etc...) In that case, a reviewer will request changes
   and describe them in the comment section of the PR.

   You then update your branch with new commits. We will see the PR
   changes faster if you ping the reviewer in the slack channel.

   Note that the comments *in the PR* are not used to discuss the
   *how* and *why* of that issue. These discussions are not about the
   issue itself but about *a solution* to that issue.

   Recall that discussions about the issue are good and prevent
   duplicated or wasted efforts, but they take place in the comment
   section of the related issue (see point 4), not in the PR.

   Essentially, we don't want to open discussions when the work is
   done, and there is no recourse, such that it's either accept or
   reject. We think we can do better than that, and introduce a finer
   grained acceptance, by involving *beforehand* discussions so that
   everyone is on point.



# Did you find a bug?


* Ensure that the bug was not already reported by [searching under Issues].

* Do _not_ file it as a plain GitHub issue (we use the
  issue system for our internal tasks (see Zenhub)).  If you're unable
  to find an (open) issue addressing the problem, [open a new one].
  Be sure to prefix the issue title with **[BUG]** and to include:

  - a *clear* description,
  - as much relevant information as possible, and 
  - a *code sample* or an (executable) *test case* demonstrating the expected behaviour that is not occurring.

* If possible, use the following [template to report a bug].




----

Thanks again,
/NBIS System Developers

[Zenhub]: https://www.zenhub.com
[coding guidelines from NBIS]: https://github.com/NBISweden/development-guidelines
[git rebase -i]: https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
[NBIS reviewing guidelines]: https://github.com/NBISweden/development-guidelines#how-we-do-code-reviews
[searching under Issues]: https://github.com/NBISweden/LocalEGA/issues?utf8=%E2%9C%93&q=is%3Aissue%20label%3Abug%20%5BBUG%5D%20in%3Atitle
[open a new one]: https://github.com/NBISweden/LocalEGA/issues/new?title=%5BBUG%5D
[template to report a bug]: todo
