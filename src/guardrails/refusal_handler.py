def get_refusal_response() -> str:
    """
    Return the standard, polite refusal response for non-factual or advisory queries.
    Bypasses vector database retrieval and generation.
    """
    return (
        "I am a facts-only assistant and cannot provide investment advice, recommendations, or fund comparisons. "
        "For official guidelines and educational resources, please consult a registered financial advisor or refer to "
        "the Association of Mutual Funds in India (AMFI) website: https://www.amfiindia.com/ or the Securities and "
        "Exchange Board of India (SEBI): https://www.sebi.gov.in/."
    )

if __name__ == "__main__":
    print(get_refusal_response())
