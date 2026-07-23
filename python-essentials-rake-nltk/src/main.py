from rake_nltk import Rake

TEXT = """
Python is a high level general purpose programming language. Its design
philosophy emphasizes code readability with the use of significant
indentation. Python is dynamically typed and garbage collected. It supports
multiple programming paradigms including structured, object oriented and
functional programming. The language is often described as a batteries
included language due to its comprehensive standard library.
"""


def main() -> None:
    rake = Rake()
    rake.extract_keywords_from_text(TEXT)
    print("ranked keywords:")
    for score, phrase in rake.get_ranked_phrases_with_scores()[:10]:
        print(f"  {score:.1f}  {phrase}")


if __name__ == "__main__":
    main()
