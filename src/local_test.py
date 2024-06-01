from poc.chains import ChainsManager

if __name__ == "__main__":
    chains_manager = ChainsManager()
    user_msg = "I want to order 2 apples."
    response = chains_manager.main(user_msg)

    print(f"Finsihed! response: {response}")

    print("Done!")
