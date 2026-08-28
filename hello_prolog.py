import janus_swi as janus

def test_janus():
    # Run a simple query to ensure janus-swi works
    result = janus.query_once("member(X, [hello, prolog, world])")
    print(f"Janus SWI test result: {result}")
    
    # Define a simple dynamic predicate
    janus.query_once("assertz(hello(world))")
    result_hello = janus.query_once("hello(X)")
    print(f"Assertz test result: {result_hello}")

if __name__ == "__main__":
    test_janus()
