ENV=prd
VERSION=6

HABOR_ID={{myapplesm}}
HABOR_PW={{59flnfdcLDbaDxNm8Qafk7URGAhq9JSS}}

IMAGE_TAG=${ENV}-${VERSION}
ECR_ROOT=mysuni-registry.mysuni.cloudzcp.net
REPOSITORY_URI=${ECR_ROOT}/mysuni-carr-prd/career-playwright
IMAGE_URI="${REPOSITORY_URI}:${IMAGE_TAG}"

docker login -u ${HABOR_ID} -p ${HABOR_PW} ${ECR_ROOT}
docker build -f Dockerfile --tag=${IMAGE_URI} .
echo "Pushing the docker image"
docker push ${IMAGE_URI}
