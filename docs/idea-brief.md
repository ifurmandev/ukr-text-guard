---
status: Draft
owner: "Ihor Furman"
updated_at: "2026-10-03"
depth: "medium"
---

# Idea brief — ukr-text-guard-quality

## 1. Raw idea

Хочу підвищити якість маркетплейсу ukr-text-guard (детектор і редактор українських текстів на ознаки ШІ): зробити детектор вимірюваним через eval з очікуваними діапазонами, прибрати дублювання analyze.py і довідників між трьома плагінами та додати хук, який автоматично запускає перевірку для українських текстів. Це для мене як автора плагіна і для користувачів маркетплейсу ifurman.

## 2. Problem

The owner does not know whether the detector works: there is no measurement of how it scores honest human texts versus AI texts. The same analysis script and reference lists are copied across three plugins, so every fix has to be made in several places. Users have to remember to run the check themselves, so Ukrainian texts go out unchecked.

## 3. Users

- The plugin author (the owner), who needs proof that the detector is right and a cheap way to maintain three plugins.
- Ukrainian-language writers who install plugins from the ifurman marketplace and run the detector and editor on their own texts (letters, articles, technical and legal documents).

## 4. Why now

No external trigger was named. The motive is internal: the detector is already in use but unmeasured, and the duplication grows with every change. Say so plainly and treat the timing as a choice, not a deadline.

## 5. Out of scope

- Changing detector rules, weights or thresholds in this iteration: that is a separate large piece of tuning and would turn «measure» into «rewrite the detector». Every false alarm and miss the eval reveals is recorded in the eval report as a known limitation for the next iteration.
- Treating bypass samples (AI text reworked to evade detectors) as pass/fail: they stay as known-gap, tracked but not required to pass.
- Renaming plugins or restructuring the marketplace: plugin names are already installed by users.
- Turning the hook on by default: it ships off and is enabled only by an explicit option.

## 6. Risks

- Assumes the owner's own texts are a fair stand-in for «human writing»; false if the detector learns one author's voice, in which case it will misfire on other people's texts and the eval will not show it. Mitigation to consider: add a few human texts by other authors.
- Assumes the expected ranges are set before looking at detector output (the owner chose this); false if the discipline slips and ranges are copied from current scores, which makes the eval mirror the detector instead of testing it.
- Assumes the false-alarm rate on human texts can end up low enough for the hook to be enabled; false if the eval shows high false alarms and rules are frozen this iteration, in which case the hook stays off and the third part of the idea delivers little.
- The human set grows gradually, so early eval runs rest on few texts and the numbers will be noisy.
- Each plugin keeps its own physical copy of the shared files; the sync check protects against drift only if it actually runs before every commit or in the eval run.

## 7. Recommendation

Do it in sequence, each step as its own commit: first the eval (expected ranges fixed before the run, priority on never labelling honest human texts as AI, bypass kept as known-gap), then the shared source with a sync script and a check that fails on any divergence, then a quiet hook that is off by default, with its text-length and score thresholds taken from the eval results. Update the eval table in the README right after the first step, showing expected ranges and known-gap status, so users see measured quality early.

## 8. Open questions

- Which score threshold and minimum text length make the hook quiet enough? — owner: Ihor Furman, answered by the first eval results.
- Where do human texts by other authors come from, to reduce the one-voice risk? — owner: Ihor Furman.
- Where does the sync check run (before commit, in the eval run, or both)? — owner: Ihor Furman, to settle in specify.
