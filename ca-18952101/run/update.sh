#!/usr/bin/env bash

VERSION=$1

printf "Update the Provision Docker VERSION:%s\n" "$VERSION"

pushd /home/mt/mt/src/embedded

unzip -o /home/mt/mt/src/embedded/release/provision_docker-$VERSION.zip

popd
