#!/usr/bin/env bats


@test "addition using bc" {
    result="$(echo 2+2 | bc)"
    [ "$result" -eq 4 ]
}

@test "echo hello world" {
    run echo "Hello World"
    [ "$output" = 'Hello World' ]
}
