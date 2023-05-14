#!/usr/bin/env bash

# This script can be called to run a build/test/command inside the Docker
# build environment container.

# TODO: Currently the host system needs to install qemu-user-static
# or the chroots will fail with an 'Exec format error'. I think this
# means it just can't find qemu-user-static in the path. How can we
# avoid this dependency on the host? Everything should be self-contained
# in the container.
# Looks like this is a kernel issue - the kernel (host and container are
# are shared) does the QEMU binary translating. There are ways to avoid
# this kernel dependency
# see: https://resin.io/blog/building-arm-containers-on-any-x86-machine-even-dockerhub/

set -eEo pipefail

USAGE="usage: ./run.sh <COMMAND> <TARGET> [notty]"

COMMAND=$1
TARGET=$2
INTERACTIVE=$3    # Default to on, Set this to "notty" if the host does not provide a TTY (i.e Jenkins)
CUID=${CUID:-$(id -u)}
CGID=${CGID:-$(id -g)}

DOCKER_IMAGE="${TARGET}-run"

# path variables needed early on
EMBEDDED_PATH="mt/src/embedded"

# Check that a command was provided
if [ "$COMMAND" == "" ]; then
    echo "Argument 1 must be a command"
    echo $USAGE
    exit 1
fi

if [ "$COMMAND" == "-h" ]; then
    echo $USAGE
    exit 0
fi

# Check that a target was given
if [ "$TARGET" == "" ]; then
    echo "Argument 2 must be a target"
    echo $USAGE
    exit 1
fi

# big hammer
if [ "${COMMAND}" == "nuke" ]; then
    if [ "${TARGET}" == "docker" ]; then
        echo "Clearing the Docker cache..."
        docker rm $(docker ps -aq)
        docker rmi -f $(docker images -aq)
        echo "Docker cache has been cleared!"
        exit 0
    fi
fi

# Get the path to the target's run directory
RUN_PATH="${TARGET}/run"

# Get all the actions for a target
if [ "$COMMAND" == "actions" ]; then
    ls ${RUN_PATH}/*.sh | tr '\n' '\0' | xargs -0 -n 1 basename | cut -f 1 -d '.'
    exit 0
fi

DOCKER_BUILD_ARGS+=(--build-arg UID="${CUID}")
DOCKER_BUILD_ARGS+=(--build-arg GID="${CGID}")

# Target can append to the DOCKER_BUILD_ARGS
if [[ -f "${RUN_PATH}/utils/host_docker_build_args.sh" ]]; then
    . ${RUN_PATH}/utils/host_docker_build_args.sh
fi

# set up mount paths
KTMR_MOUNT_PATH="/home/mt"
EMBEDDED_MOUNT_PATH="${KTMR_MOUNT_PATH}/${EMBEDDED_PATH}"

# build up the path to the script to run
SCRIPT_PATH="${RUN_PATH}/${COMMAND}.sh"

# Arguments common to all docker run calls

# Docker volumes to be mounted on all containers
DOCKER_VOLUMES=(-v "`pwd`":"${EMBEDDED_MOUNT_PATH}")

# Darwin specific handling of volumes
case "$(uname -s)" in

  Darwin)
    _i_count=${#DOCKER_VOLUMES[@]}
    for ((ii=0;ii<_i_count;ii++)); do
        DOCKER_VOLUMES[ii]="${DOCKER_VOLUMES[ii]}:delegated"
    done
  ;;

  Linux)
  ;;

  *)
  echo "Unsupported OS: $(uname -s)"
  exit 1
  ;;
esac

if [ "$COMMAND" = "get" ]; then
    echo "Running $COMMAND for $TARGET outside of Docker"
    bash "${KTMR_PATH}/${EMBEDDED_PATH}/${SCRIPT_PATH}"

elif [ "$COMMAND" = "bash" ]; then
    # Don't run any build scripts, just open an interactive bash prompt
    # This should rarely be needed - it is here as a convenience
    echo "Opening interactive bash prompt in container"
    docker run \
    -it \
    --privileged \
    -v /dev/bus/usb/:/dev/bus/usb \
    "${DOCKER_VOLUMES[@]}" \
    "${DOCKER_RUN_ARGS[@]}" \
    "$DOCKER_IMAGE" \
    bash

elif [ "$COMMAND" = "build_image" ]; then
    echo "Building Docker image..."
    DOCKER_BUILDKIT=1 docker build \
        --rm \
        "${DOCKER_BUILD_ARGS[@]}" \
        -t "$DOCKER_IMAGE" \
        -f - tools < "tools/docker/${TARGET}/Dockerfile"

    if [ $? != 0 ]; then
        echo "ERROR: Failed to build Docker image."
        exit 1
    fi
else
    # Typical builds require fewer privileges
    # echo "Running $COMMAND for $TARGET"

    # set up the TTY arg
    if [ "$INTERACTIVE" != "notty" ]; then
      # echo "Running with interactive console"
      DOCKER_RUN_ARGS+=(-it)
    fi

    # use the hostname
    DOCKER_RUN_ARGS+=(-h $(hostname))

    # if TARGET = lbb ; need to mount /dev for loopback
    if [ "${TARGET}" = "lbb" ]; then
      echo "Mount volume /dev for ${TARGET}"
      DOCKER_RUN_ARGS+=(-v "/dev:/dev")
    fi

    docker run \
      --privileged \
      "${DOCKER_VOLUMES[@]}" \
      "${DOCKER_RUN_ARGS[@]}" \
      "$DOCKER_IMAGE" \
      bash "${EMBEDDED_MOUNT_PATH}/${SCRIPT_PATH}"
fi

if [ $? != 0 ] && [ "$COMMAND" != "bash" ]; then
    echo "ERROR: Script failed in Docker container."
    exit 1
else
    echo "SUCCESS: Script finished successfully in Docker container."
    exit 0
fi
