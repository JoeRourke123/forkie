#!/bin/bash

# Hardcoded environment vars (this was fixed for older versions of bash (v3) using info from: https://stackoverflow.com/questions/6047648/bash-4-associative-arrays-error-declare-a-invalid-option)
ENVIRONMENT_VARS=(
    "APPLICATION_KEY::K0000L+ZHdPrf3wT4G+7enptKGSct68"
    "APPLICATION_KEY_ID::0003976a482cd540000000001"
    "BUCKET_NAME::file-rep0"
    "DATABASE_URL::postgres://viiifcyupwxvin:d8262ffd64dca62a110b013fa939c6a08a553f08aee223d315fa8428d58a88b8@ec2-54-247-177-254.eu-west-1.compute.amazonaws.com:5432/dfqgciolfgj7gg"
    "SENDGRID_API_KEY::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"
    "SENDGRID_PASSWORD::kzaidkww3818"
    "SENDGRID_USERNAME::app159507625@heroku.com"
)

if [ ! -f "Procfile" ]; then
    echo "Procfile doesn't exist in the current directory. Are you sure this is a forkie dir"
    exit 1
fi

echo "Exporting environment variables"
for i in "${ENVIRONMENT_VARS[@]}"; do
    # Splits index at the "::" key on left and value on right
    KEY="${i%%::*}"
    VALUE="${i##*::}"
    echo "$KEY=$VALUE"
    export "$KEY=$VALUE"
done

# set -x
heroku local web

exit 1