import csv
import logging
import os
import re
from collections import Counter

"""
Run this script with:
    python3 analyse_reviews.py

Input: 
    None

Output:
    dataset.csv (dataset with all reviews)
    create_dataset.log (logfile for this script, you can change the log-level below to debug)
"""

# see https://docs.python.org/3/howto/logging.html
logging.basicConfig(filename='create_dataset.log', format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filemode='w', level=logging.ERROR)


def get_review_files(review_path):
    """ get all finished reviews """
    reviews = os.listdir(review_path)
    # filter out our template, rejected papers, currently reviewed papers and scripts
    reviews = [r for r in reviews if not any(["TBD.md" in r, "TODO.md" in r, "hypotheses.md" in r,
                                              "REJECT" in r, ".sh" in r, "pymupdf_high" in r,
                                              r == "rejected"])]
    logging.info(f"Parsed {len(reviews)} reviews")
    return reviews


def write_dataset_to_csv(all_reviews, fieldnames):
    with open("dataset.csv", "a", encoding='utf-8') as dataset_file:
        dict_writer = csv.DictWriter(dataset_file, fieldnames=fieldnames, delimiter=";")
        for ar in all_reviews:
            dict_writer.writerow(ar)


def rename_fields_by_hnr(line, new_other, new_other_begin, i, ml_str, header=False):
    # template has no x, so different approach
    if header:
        line = line.replace("- [O]", "").replace("- [", "").replace("]", "").replace(":", "")
        line = line.strip()
        line = re.sub(r"^-", "", line).strip()
    # some free text in other fields mentions hypotheses_nr
    if "OTHER" not in line:
        # get H number
        h_nr = re.search(r"H\d{1,2} ", line)
        if h_nr:
            h_nr = h_nr[0].strip()
            new_other = f"_{h_nr}"
    header_strs = {"supervised": " (supervised)", "unsupervised": " (unsupervised)"}
    # case 1
    if header:
        if line == "OTHER" and new_other != "":
            line += new_other
        elif line == "OTHER" and new_other == "":
            line += "_" + new_other_begin.get(i)
            i += 1
        ml_str = header_strs[line] if line in header_strs else ml_str
        if line == "Neural Networks":
            line += ml_str
    # case 2
    elif not header:
        if "OTHER" in line and new_other != "":
            line = line.replace("OTHER", "OTHER" + new_other)
        elif "OTHER" in line and new_other == "":
            line = line.replace("OTHER:", "OTHER_" + new_other_begin.get(i) + ":")
            i += 1
        if "] supervised" in line:
            ml_str = " (supervised)"
        elif "] unsupervised" in line:
            ml_str = " (unsupervised)"
        if "] Neural Networks" in line:
            line = line.replace("Neural Networks", "Neural Networks" + ml_str)
    else:
        raise ValueError
    return line, i, ml_str, new_other


def write_csv_header_from_template(review_path):
    template = os.path.join(review_path, "hypotheses.md")
    all_fields = []
    with open(template, encoding='utf-8') as f:
        new_other = ""
        new_other_begin = {0: "dataset", 1: "supervised", 2: "unsupervised", 3: "utilized_model"}
        i = 0
        # to remove duplicate NN
        ml_str = ""
        for line in f:
            skip_line = check_skip_line(line)
            if skip_line:
                continue
            elif ("-" in line and "]" in line) or ":" in line:
                # rename other according to hypothesis number
                line, i, ml_str, new_other = rename_fields_by_hnr(line, new_other, new_other_begin, i, ml_str, True)
                if line not in all_fields:
                    all_fields.append(line)
    all_fields.append("bib-acronym")
    with open("dataset.csv", "a", encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(all_fields)


def check_skip_line(line):
    if line.isspace():
        return True
    elif line.startswith("[//]:"):
        return True


def set_hypotheses_and_rest(match_elem, r, new_review, field):
    match_elem = match_elem.replace("- [x]", "").replace("- [X]", "").strip()
    if match_elem in new_review:
        new_review[match_elem] = 1
        logging.info(f"Set {match_elem}: {new_review[match_elem]}")
    else:
        logging.error(f"Did not find field for hypotheses: {r}, {field}")
    return new_review


def set_general_info_and_other(match_elem, r, new_review, field):
    # handle first boxes before hypotheses
    if "[x]" not in match_elem and "[X]" not in match_elem and "[ ]" not in match_elem and \
            "[]" not in match_elem:
        match_elem = match_elem.replace("- ", "").split(":")
        key, val = match_elem[0].strip(), match_elem[1:]
    else:
        # handle other fields, we also write other fields to CSV if not ticked
        match_elem = match_elem.replace("- [x] ", "").replace("- [X] ", "").replace("- [ ] ", "").split(":")
        key, val = match_elem[0].strip(), match_elem[1:]
    if key in new_review:
        new_val = ""
        for i, v in enumerate(val):
            if i == len(val) - 1:
                new_val += v
            else:
                new_val += v + ":"
        if new_val != "":
            new_review[key] = new_val.strip()
            logging.info(f"Set {key}: {new_review[key]}")
        elif key in ("paper title", "conference/journal", "year", "bib-acronym") and new_val == "":
            logging.error(f"No value for {key} in {r}")
    else:
        logging.error(f"Key not in review {r}, {field}, {key}, {match_elem}")
    return new_review


def set_review_attributes(match_elem, new_review, r, field, ticked):
    if "[O]" in match_elem or "[o]" in match_elem:
        logging.error(f"Field {field} not handled in review {r}")
    # some reviews have comments behind fields, drop them for matching
    match_elem = match_elem.split("#")[0].strip()
    check = match_elem.split(":")
    if ":" in match_elem and len(check) > 2:
        if "OTHER" not in check[0] and "paper title" not in check[0]:
            logging.error(f"Other colon than seperator at beginning {check[0]} in {r}")
    # set general information and other fields
    if ":" in match_elem:
        new_review = set_general_info_and_other(match_elem, r, new_review, field)
    # set hypotheses and rest
    elif ("[x]" in match_elem or "[X]" in match_elem or ticked) and "OTHER" not in match_elem:
        new_review = set_hypotheses_and_rest(match_elem, r, new_review, field)
    return new_review


def select_match_from_multiple(match, field, ticked):
    # check for exact match
    for i, elem in enumerate(match):
        # store if matches are ticked
        ticked = False
        if "[x]" in elem or "[X]" in elem:
            ticked = 1
        # format match so that it might fit to the field
        clean_line = elem.replace("- [x] ", "").replace("- [X] ", "").replace("- [ ] ", "").replace(
            "- [ ] ", "").replace("- ", "")
        match[i] = (clean_line, ticked)
    match = [(m, is_ticked) for (m, is_ticked) in match if field == m.split(":")[0]]
    # if exact match not found for field, throw error
    if not match or len(match) > 1:
        if len(Counter(match)) > 1:
            raise ValueError("Duplicate Field ticked differently!")
    match, ticked = match[0]
    return match, ticked


def find_field_in_content(r, field, content):
    # check if field in any line of the review
    match = [li for li in content if field in li]
    if field == "bib-acronym":
        tokens = r.split('_')
        bib_acronym = "".join(tokens[0:2])
        match = ["bib-acronym: " + bib_acronym]
    ticked = False
    # field not found in review
    if not match:
        return None, None, False
    # exactly one match
    elif len(match) == 1:
        match = match[0]
    # if more than one line with field found
    elif len(match) > 1:
        match, ticked = select_match_from_multiple(match, field, ticked)
    return match, ticked, True


def read_review_for_dataset(review_path, r):
    # read the review and give the OTHER fields unique names
    with open(os.path.join(review_path, r), "r", encoding='utf-8') as f:
        new_other = ""
        new_other_begin = {0: "dataset", 1: "supervised", 2: "unsupervised", 3: "utilized_model"}
        i = 0
        content = []
        # to remove duplicate NN
        ml_str = ""
        for line in f:
            # filter out emtpy lines and instructions to fill review out
            skip_line = check_skip_line(line)
            if skip_line:
                continue
            elif ("-" in line and "]" in line) or ":" in line:
                # rename other according to hypothesis number
                line, i, ml_str, new_other = rename_fields_by_hnr(line, new_other, new_other_begin, i, ml_str, False)
                content.append(line.strip())
    return content


def create_dataset(review_path, reviews):
    with open("dataset.csv", encoding='utf-8') as dataset:
        csv_reader = csv.DictReader(dataset, delimiter=";")
        fieldnames = [key for key in csv_reader.fieldnames]
        all_reviews = []
        # check if hypotheses are ticked
        for review_name in reviews:
            logging.info(f"Begin Review: {review_name}")
            # prepare dataset entry
            new_review = {key: None for key in fieldnames}
            # read the review and give the OTHER fields unique names
            content = read_review_for_dataset(review_path, review_name)
            # check each field for a review
            for field in fieldnames:
                # find correct field in review
                logging.debug(f"Field: {field}")
                found_field, ticked, found = find_field_in_content(review_name, field, content)
                logging.debug(f"Found {found_field}")
                if not found:
                    logging.error(f"Did not find field '{field}' for {review_name}")
                    continue
                try:
                    # set all values in the resulting CSV file
                    new_review = set_review_attributes(found_field, new_review, review_name, field, ticked)
                except:
                    raise ValueError
            all_reviews.append(new_review)
    return all_reviews, fieldnames


def main():
    # TODO: update old reviews
    review_path = os.path.join("reviews", "reviews")
    if os.path.exists("dataset.csv"):
        os.remove("dataset.csv")
    reviews = get_review_files(review_path)
    write_csv_header_from_template(review_path)
    all_reviews, fieldnames = create_dataset(review_path, reviews)
    write_dataset_to_csv(all_reviews, fieldnames)


if __name__ == '__main__':
    main()
