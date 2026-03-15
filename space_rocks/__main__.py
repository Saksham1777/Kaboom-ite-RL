from game import SpaceRocks

if __name__ == "__main__":
    space_rocks = SpaceRocks()
    try:
        space_rocks.main_loop()
    except Exception as e:
        print(f"Game crashed error {e}")
        input("press enter to close")