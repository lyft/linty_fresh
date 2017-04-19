licenses(["notice"])

package(default_visibility = ["//visibility:public"])

pex_library(
    name = "pytest",
    eggs = ["//external:wheel/pytest"],
    deps = ["//third_party/py:py"],
)

pex_binary(
    name = "runner",
    deps = [":pytest"],
    entrypoint = "pytest")
