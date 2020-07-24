from .engine.pathsobserver import PathsObserver

paths_observer = PathsObserver()

if __name__ == "__main__":

    paths_observer.start()

    try:
        while paths_observer.is_alive():
            paths_observer.join(1)
    except KeyboardInterrupt:
        paths_observer.stop()

    paths_observer.join()
