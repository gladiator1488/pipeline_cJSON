cmake_minimum_required(VERSION 3.10)
project(PetCIWrapper)


enable_testing()


add_subdirectory(cJSON)


set(CPACK_PACKAGE_NAME "cjson")
set(CPACK_PACKAGE_CONTACT "devops@x5.ru")
include(CPack)