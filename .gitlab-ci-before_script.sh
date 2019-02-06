set -eu

# Install helm and its dependencies. The version of helm and kubectl must be
# specified via the following environment variables:
#   * `HELM_VERSION`: The version of helm to install
#   * `HELM_CHECKSUM`: The SHA-256 checksum of the helm archive
#   * `K8S_VERSION`: The Kubernetes version kubectl will interact with
#   * `KUBECTL_CHECKSUM`: The SHA-256 checksum of the kubectl executable
function install_helm {
  if [[ -z "$K8S_VERSION" ]] || [[ -z "$KUBECTL_CHECKSUM" ]] \
      || [[ -z "$HELM_VERSION" ]] || [[ -z "$HELM_CHECKSUM" ]]; then
    1>&2 echo -e \
        'The following environment variables must be set to install Helm:\n' \
        ' * HELM_VERSION: The version of helm to install\n' \
        ' * HELM_CHECKSUM: The SHA-256 checksum of the helm archive\n' \
        ' * K8S_VERSION: The Kubernetes version kubectl will interact with\n' \
        ' * KUBECTL_CHECKSUM: The SHA-256 checksum of the kubectl executable'
    return 1
  fi
  apk add -U curl openssl ca-certificates

  local temp_dir=$(mktemp -d)
  ( # Subshell to use temporary working directory.
    cd "$temp_dir"

    # Install kubectl
    curl -LO "https://storage.googleapis.com/kubernetes-release/release/v$K8S_VERSION/bin/linux/amd64/kubectl"
    echo -n "$KUBECTL_CHECKSUM  kubectl" | sha256sum -c
    chmod +x kubectl
    mv kubectl /usr/local/bin/
    echo 'kubectl version'
    kubectl version --client

    # Install helm
    local helm_archive="helm-v$HELM_VERSION-linux-amd64.tar.gz"
    curl -LO "https://storage.googleapis.com/kubernetes-helm/$helm_archive"
    echo -n "$HELM_CHECKSUM  $helm_archive" | sha256sum -c
    tar -xzf $helm_archive
    mv linux-amd64/helm /usr/local/bin/
    echo 'helm version'
    helm version --client
    helm init --client-only
  )
  rm -rf "$temp_dir"
}

# Login to the CI Docker registry using the registry information and credentials
# provided by the GitLab CI environment. If no such information is available
# then this function is a no-op.
function docker_login {
  if [[ -n "$ARTIFACTORY_USER" ]]; then
    echo "Login to Docker registry $ARTIFACTORY_URL…"
    docker login -u "$ARTIFACTORY_USER" -p "$ARTIFACTORY_PASSWORD" \
      "$ARTIFACTORY_URL"
  fi
}

# Build a docker image at the specified path. A default Dockerfile is assumed to
# be present at the root of that path. Additionally, a component name may be
# specified which will be appended to the resulting image name.
#
# Built images are pushed to the registry with the current ref (e.g. branch)
# name as an additional qualifier in the image name.
#
# Usage: docker_build PATH [COMPONENT_NAME]
function docker_build {
  if [[ -z "$1" ]]; then
    1>&2 echo -e \
        'No path specified for Docker build context. If your Dockerfile is' \
        '\nat the root of the project then you can use "." as the path.'
    return 1
  fi
  docker_login

  local image_name="$ARTIFACTORY_URL/$ARTIFACTORY_REPOSITORY"
  #image_name="$image_name/pre-release:$CI_COMMIT_SHA"

  echo "Build image $image_name…"
  docker build "$1" -t "$image_name:$CI_COMMIT_SHA" -t "$image_name:latest" \
  --build-arg REPO_PREFIX="$ARTIFACTORY_URL/docker-remote/"

  echo "Push image $image_name…"
  docker push "$image_name:$CI_COMMIT_SHA"
  docker push "$image_name:latest"
}

# Push production images to the CI Docker registry. The specified components
# built by `docker_build` will be tagged and pushed without the additional ref
# name qualifier (i.e. under the project's root name). If no component name is
# specified, then a single root image is assumed.
#
# Each pushed image will also be tagged as `latest`.
#
# Usage: docker_release [COMPONENT_NAME...]
function docker_release {
  docker_login

  while true; do
    local source_image_tagged="$ARTIFACTORY_URL/$ARTIFACTORY_REPOSITORY"
    local target_image="$ARTIFACTORY_URL/$ARTIFACTORY_REPOSITORY"
    # Append component name if present.
    if [[ -n "$1" ]]; then
      source_image_tagged="$source_image_tagged/$1"
      target_image="$target_image/$1"
    fi
    source_image_tagged="$source_image_tagged/pre-release:$CI_COMMIT_SHA"

    echo "Release image $source_image_tagged as" \
      "$target_image:$CI_COMMIT_SHA (and :latest)…"
    docker pull "$source_image_tagged"
    docker tag "$source_image_tagged" "$target_image:$CI_COMMIT_SHA"
    docker tag "$target_image:$CI_COMMIT_SHA" "$target_image:latest"
    docker push "$target_image:$CI_COMMIT_SHA"
    docker push "$target_image:latest"

    # Break once all components are pushed.
    shift && [[ $# == 0 ]] && break
  done
}

