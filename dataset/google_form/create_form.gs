/**
 * Creates the 4 data-collection Google Forms (A, B, C, D) for our dataset of beginner Python mistakes.
 * Each form has 5 different MBPP problems (about 15 minutes per student).
 *
 * How to run: script.google.com -> New project -> paste this file -> Run createAllForms()
 * -> allow permissions. The four form links appear in View -> Logs.
 * All four forms save into ONE Google Sheet (one tab per form).
 *
 * PROBLEMS is copied from dataset/problems.json (MBPP sanitized split, unchanged wording).
 */

const PROBLEMS = [
  {
    "mbpp_task_id": 600,
    "form": "A",
    "prompt": "Write a python function to check whether the given number is even or not.",
    "function_name": "is_Even",
    "examples": [
      "is_Even(1)  should return  False",
      "is_Even(2)  should return  True"
    ]
  },
  {
    "mbpp_task_id": 567,
    "form": "A",
    "prompt": "Write a function to check whether a specified list is sorted or not.",
    "function_name": "issort_list",
    "examples": [
      "issort_list([1,2,4,6,8,10,12,14,16,17])  should return  True",
      "issort_list([1, 2, 4, 6, 8, 10, 12, 14, 20, 17])  should return  False"
    ]
  },
  {
    "mbpp_task_id": 566,
    "form": "A",
    "prompt": "Write a function to get the sum of the digits of a non-negative integer.",
    "function_name": "sum_digits",
    "examples": [
      "sum_digits(345)  should return  12",
      "sum_digits(12)  should return  3"
    ]
  },
  {
    "mbpp_task_id": 172,
    "form": "A",
    "prompt": "Write a function to count the number of occurence of the string 'std' in a given string.",
    "function_name": "count_occurance",
    "examples": [
      "count_occurance(\"letstdlenstdporstd\")  should return  3",
      "count_occurance(\"stds\")  should return  1"
    ]
  },
  {
    "mbpp_task_id": 755,
    "form": "A",
    "prompt": "Write a function to find the second smallest number in a list.",
    "function_name": "second_smallest",
    "examples": [
      "second_smallest([1, 2, -8, -2, 0, -2])  should return  -2",
      "second_smallest([2,2])  should return  None"
    ]
  },
  {
    "mbpp_task_id": 227,
    "form": "B",
    "prompt": "Write a function to find minimum of three numbers.",
    "function_name": "min_of_three",
    "examples": [
      "min_of_three(10,20,0)  should return  0",
      "min_of_three(19,15,18)  should return  15"
    ]
  },
  {
    "mbpp_task_id": 461,
    "form": "B",
    "prompt": "Write a python function to count the upper case characters in a given string.",
    "function_name": "upper_ctr",
    "examples": [
      "upper_ctr('PYthon')  should return  1",
      "upper_ctr('program')  should return  0"
    ]
  },
  {
    "mbpp_task_id": 412,
    "form": "B",
    "prompt": "Write a python function to remove odd numbers from a given list.",
    "function_name": "remove_odd",
    "examples": [
      "remove_odd([1,2,3])  should return  [2]",
      "remove_odd([10,20,3])  should return  [10,20]"
    ]
  },
  {
    "mbpp_task_id": 88,
    "form": "B",
    "prompt": "Write a function to get the frequency of all the elements in a list, returned as a dictionary.",
    "function_name": "freq_count",
    "examples": [
      "freq_count([1,2,3,4,3,2,4,1,3,1,4])  should return  {1:3, 2:2,3:3,4:3}"
    ]
  },
  {
    "mbpp_task_id": 632,
    "form": "B",
    "prompt": "Write a python function to move all zeroes to the end of the given list.",
    "function_name": "move_zero",
    "examples": [
      "move_zero([1,0,2,0,3,4])  should return  [1,2,3,4,0,0]",
      "move_zero([0,1,0,1,1])  should return  [1,1,1,0,0]"
    ]
  },
  {
    "mbpp_task_id": 599,
    "form": "C",
    "prompt": "Write a function to find sum and average of first n natural numbers.",
    "function_name": "sum_average",
    "examples": [
      "sum_average(10)  should return  (55, 5.5)",
      "sum_average(15)  should return  (120, 8.0)"
    ]
  },
  {
    "mbpp_task_id": 796,
    "form": "C",
    "prompt": "Write function to find the sum of all items in the given dictionary.",
    "function_name": "return_sum",
    "examples": [
      "return_sum({'a': 100, 'b':200, 'c':300})  should return  600",
      "return_sum({'a': 25, 'b':18, 'c':45})  should return  88"
    ]
  },
  {
    "mbpp_task_id": 58,
    "form": "C",
    "prompt": "Write a python function to check whether the given two integers have opposite sign or not.",
    "function_name": "opposite_Signs",
    "examples": [
      "opposite_Signs(1,-2)  should return  True",
      "opposite_Signs(-10,-10)  should return  False"
    ]
  },
  {
    "mbpp_task_id": 604,
    "form": "C",
    "prompt": "Write a function to reverse words seperated by spaces in a given string.",
    "function_name": "reverse_words",
    "examples": [
      "reverse_words(\"python program\")  should return  \"program python\"",
      "reverse_words(\"java language\")  should return  \"language java\""
    ]
  },
  {
    "mbpp_task_id": 395,
    "form": "C",
    "prompt": "Write a python function to find the first non-repeated character in a given string.",
    "function_name": "first_non_repeating_character",
    "examples": [
      "first_non_repeating_character(\"abcabc\")  should return  None",
      "first_non_repeating_character(\"abc\")  should return  \"a\""
    ]
  },
  {
    "mbpp_task_id": 66,
    "form": "D",
    "prompt": "Write a python function to count the number of positive numbers in a list.",
    "function_name": "pos_count",
    "examples": [
      "pos_count([1,-2,3,-4])  should return  2",
      "pos_count([3,4,5,-1])  should return  3"
    ]
  },
  {
    "mbpp_task_id": 605,
    "form": "D",
    "prompt": "Write a function to check if the given integer is a prime number.",
    "function_name": "prime_num",
    "examples": [
      "prime_num(13)  should return  True",
      "prime_num(-1010)  should return  False"
    ]
  },
  {
    "mbpp_task_id": 577,
    "form": "D",
    "prompt": "Write a python function to find the last digit in factorial of a given number.",
    "function_name": "last_Digit_Factorial",
    "examples": [
      "last_Digit_Factorial(4)  should return  4",
      "last_Digit_Factorial(21)  should return  0"
    ]
  },
  {
    "mbpp_task_id": 277,
    "form": "D",
    "prompt": "Write a function that takes in a dictionary and integer n and filters the dictionary to only include entries with values greater than or equal to n.",
    "function_name": "dict_filter",
    "examples": [
      "dict_filter({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Kierra Gentry': 165, 'Pierre Cox': 190},170)  should return  {'Cierra Vega': 175, 'Alden Cantrell': 180, 'Pierre Cox': 190}"
    ]
  },
  {
    "mbpp_task_id": 602,
    "form": "D",
    "prompt": "Write a python function to find the first repeated character in a given string.",
    "function_name": "first_repeated_char",
    "examples": [
      "first_repeated_char(\"abcabc\")  should return  \"a\"",
      "first_repeated_char(\"abc\")  should return  None"
    ]
  }
];

function createAllForms() {
  const sheet = SpreadsheetApp.create('Beginner Attempts - Responses');
  ['A', 'B', 'C', 'D'].forEach(function (formId) {
    const problems = PROBLEMS.filter(function (p) { return p.form === formId; });
    const form = createForm(formId, problems);
    form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
    Logger.log('Form ' + formId + ' share link:  ' + form.getPublishedUrl());
    Logger.log('Form ' + formId + ' edit link:   ' + form.getEditUrl());
  });
  Logger.log('Responses sheet:  ' + sheet.getUrl());
}

function createForm(formId, problems) {
  const form = FormApp.create('Python Practice - Form ' + formId);
  form.setDescription(
    'Hi! We are 7th-semester ISE students at MSRIT building an AI tutor that helps beginners ' +
    'learn Python by giving hints instead of full answers. To build it, we need real first ' +
    'attempts by beginners, and wrong answers are the most useful to us. ' +
    'There are 5 small problems; it takes about 15 minutes.'
  );
  form.setProgressBar(true);
  form.setConfirmationMessage('Thank you! Your attempts will help us build a better tutor for beginners.');

  form.addCheckboxItem()
    .setTitle('Consent')
    .setChoiceValues(['I agree. I understand my answers are anonymous and will be used only for this college project and its report.'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Year of study')
    .setChoiceValues(['1st year', '2nd year', '3rd year', '4th year'])
    .showOtherOption(true)
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('Before you start')
    .setHelpText(
      '1. Write your FIRST attempt. Do NOT run your code.\n' +
      '2. Do NOT use ChatGPT, Gemini, Copilot, Google or any other help.\n' +
      '3. Write the full function, starting with "def". Use spaces for indentation.\n' +
      '4. If you have no idea at all, leave the box blank. Otherwise give it your honest best try.'
    );

  problems.forEach(function (p, i) {
    form.addParagraphTextItem()
      .setTitle('Problem ' + (i + 1) + ': ' + p.prompt)
      .setHelpText(
        'Function name: ' + p.function_name + '\n' +
        'Examples:\n  ' + p.examples.join('\n  ') + '\n\n' +
        '[MBPP ' + p.mbpp_task_id + ']'
      );
  });

  return form;
}
