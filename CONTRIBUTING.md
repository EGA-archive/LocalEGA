# Contributing guidelines

This document describes how to contribute to the Local EGA project

We thank you in advance :+1::tada: for taking the time to contribute whether with _code_ or with _ideas_.

## AGILE project management

We use [Zenhub](https://www.zenhub.com/), the Agile project management within Github.

You should first [install it](https://www.zenhub.com/extension) if you want to contribute or just follow the project progress.  
You can also use the [Zenhub app](https://app.zenhub.com) if you wish.

In short, the [AGILE method](https://www.zenhub.com/blog/how-to-use-github-agile-project-management/) helps developers organize themselves:

* They decide about the tasks (not the managers)
* Main Tasks should be divided into smaller manageable ones. The big
  tasks are called `Epics`.
* We have a given period (called Sprint) to work on a chosen
  task. Here, a Sprint spans across 2 weeks.
* We review the work done at the end of the Sprint, closing issues or
  pushing them into the next Sprint. Ideally, they are sub-divided in
  case they encounter obstacles.
* We have a short meeting every weekday at 9:30 AM. We call it a
  _standup_ and we use it to keep everyone on point, and identify
  quickly blockers. It's not a lengthy discussion. We ask:
    - What did you get done yesterday (or last week, last month, etc.)?
    - What are you working on now?
    - What isn’t going well, and on what could you use help?

## Procedure

1) Create an issue on Github, and talk to the team members on the NBIS
   local-ega Slack channel. You can alternatively pick one already
   created.

>   Contact
>   [Jonas Hagberg](https://nbis.se/about/staff/jonas-hagberg/) to
>   request access if you are not part of that channel already.

2) Assign yourself to that issue.

3) Discussions on how to proceed about that issue take place in the
   comment section on that issue, beforehand.  
   
   The keyword here is _beforehand_. It is usually a good idea to talk
   about it first. Somebody might have already some pieces in place,
   we avoid unnecessary work duplication and a waste of time and
   effort.

4) Work on it (on a fork, or on a separate branch) as you wish. That's
what `git` is good for. This GitHub repository follows
the [coding guidelines from NBIS](/NBISweden/development-guidelines).
   
   Name your branch as you wish and prefix the name with:
   * `feature/` if it is a code feature
   * `hotfix/` if you are fixing an urgent bug

   Use comments in your code, choose variable and function names that
   clearly show what you intend to implement.

   Use [`git rebase -i`](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History) in
   order to rewrite your history, and have meaningful commits.  That
   way, we avoid the 'Typo', 'Work In Progress (WIP)', or
   'Oops...forgot this or that' commits.

   Limit the first line of your git commits to 72 characters or less.


5) Create a Pull Request (PR), so that your code is reviewed by the
   admins on this repository.  
   
   That PR should be connected to the issue you are working on.
   Moreover, the PR:
   
   - should use `Estimate=1`,
   - should be connected to:
     + an `Epic`,
     + a `Milestone` and
     + a `User story`
     + ... or several.

Do **_not_** ask us to merge it into `master`. We will use the `dev` branch.

6) Selecting a review goes as follows: Pick one _main_ reviewer.  It
   is usually one that you had discussions with, and is somehow 
   connected to that issue. If this is not the case, pick several reviewers.
   
   Note that, in turn, the main reviewer might ask another reviewer
   for help. The approval of all reviewers is compulsory in order to
   merge the PR. Moreover, the main reviewer is the one merging the
   PR, not you.
   
   Find more information on the [NBIS reviewing guidelines](/NBISweden/development-guidelines#how-we-do-code-reviews).


7) It is possible that your PR requires changes (because it creates
   conflicts, or because some parts should be rewritten in a cleaner
   manner, or because it does not follow the standards, or you're
   requesting the wrong branch to pull your code, etc...) In that
   case, a reviewer will request changes and describe them in the
   comment section of the PR.

   You then update your branch with new commits and ping the reviewer
   on the slack channel. (Yes, we respond better there).

   Note that the comments _in the PR_ are not used to discuss the
   _how_ and _why_ of that issue. These discussions are not about the
   issue itself but about _a solution_ to that issue.

   Recall that discussions about the issue are good and prevent
   duplicated or wasted efforts, but they take place in the comment
   section of the related issue (see point 4), not in the PR.

   Essentially, we don't want to open discussions when the work is
   done, and there is no recourse, such that it's either accept or
   reject. We think we can do better than that, and introduce a finer
   grained acceptance, by involving _beforehand_ discussions so that
   everyone is on point.



## Did you find a bug?

* Ensure that the bug was not already reported by [searching under
  Issues](/NBISweden/LocalEGA/issues?utf8=%E2%9C%93&q=is%3Aissue%20label%3Abug%20%5BBUG%5D%20in%3Atitle).

* Do **_not_** file it as a plain GitHub issue (we use the issue
  system for our internal tasks (see Zenhub)).  If you're unable to
  find an (open) issue addressing the problem, [open a new
  one](NBISweden/LocalEGA/issues/new?title=%5BBUG%5D).  Be sure to
  prefix the issue title with **[BUG]** and to include:

  - a _clear_ description,
  - as much relevant information as possible, and 
  - a _code sample_ or an (executable) _test case_ demonstrating the expected behaviour that is not occurring.

* If possible, use the following [template to report a bug](todo) /* TODO */



----

Thanks again,  
/NBIS System Developers
