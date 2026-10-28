# Data-collection forms: setup

There are 4 forms (A, B, C, D) with 5 different MBPP problems each, 20 problems in total. Each student fills **one** form, which takes about 15 minutes.

## Which problems are in which form

Every form has 1–2 easy problems, 2–3 medium ones and 1 hard one, from different topics.

| Form | Easy | Medium | Hard |
|---|---|---|---|
| A | 600 is_Even (if/else) | 567 issort_list (lists), 566 sum_digits (loops), 172 count_occurance (strings) | 755 second_smallest (lists) |
| B | 227 min_of_three (functions), 461 upper_ctr (strings) | 412 remove_odd (lists), 88 freq_count (dicts) | 632 move_zero (lists) |
| C | 599 sum_average (functions), 796 return_sum (dicts) | 58 opposite_Signs (if/else), 604 reverse_words (strings) | 395 first_non_repeating_character (strings) |
| D | 66 pos_count (lists) | 605 prime_num (if/else), 577 last_Digit_Factorial (loops), 277 dict_filter (dicts) | 602 first_repeated_char (strings) |

Full text and all test cases are in `../problems.json`. The difficulty labels are our own judgement for beginners, not part of MBPP.

## 1. Create the forms (about 5 minutes)
1. Go to https://script.google.com, signed in with the account that should own the forms.
2. Click **New project**, delete the sample code, and paste in all of `create_form.gs`.
3. Choose `createAllForms` in the function dropdown and click **Run**. Allow the permissions Google asks for.
4. Open **View > Logs**. It shows 4 share links, 4 edit links and 1 responses sheet. The sheet gets one tab per form.

## 2. Check these settings in each form (Settings tab)
- **Collect email addresses:** Do not collect. This keeps the forms anonymous.
- **Limit to 1 response:** OFF. Turning it on forces sign-in.

## 3. Test before sharing
Submit Form A once with an indented function. Check that the indentation survived in the sheet, then delete the test row.

## 4. How many students you need

| Difficulty | Guess: share of attempts that will be wrong |
|---|---|
| Easy | ~25% |
| Medium | ~45% |
| Hard | ~65% |

These rates are guesses. With them, each student gives about **2 buggy attempts** (some boxes will be blank or correct).
- **50+ rows needs about 25 students**, so aim for **32 (8 per form)** to be safe.
- Check the sheet every day or two. If one form has fewer responses, send that link again.
- 1st- and 2nd-year students give the most useful mistakes.

## 5. WhatsApp message

> Hi everyone! 👋 We're 7th-sem ISE students working on a GenAI project, an AI tutor that helps beginners learn Python with hints instead of answers.
>
> Could you help us by solving 5 small Python problems? It takes about 15 minutes and is completely anonymous.
>
> 📌 Pick your form by your *birthday month*:
> Jan–Mar → Form A: <link A>
> Apr–Jun → Form B: <link B>
> Jul–Sep → Form C: <link C>
> Oct–Dec → Form D: <link D>
>
> Just 3 rules: write your *first attempt*, *don't run the code*, and *no ChatGPT/Google*. Wrong answers are honestly the most useful for us! 😄
>
> Thanks a lot! 🙏

Birthday month splits people roughly evenly across the four forms without collecting anything personal.

## 6. Your own old buggy code
Only use it if it solves one of these 20 problems, so every row is checked with the same tests. Mark those rows `source = authors` in the CSV.
