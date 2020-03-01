#!/bin/bash

# Hardcoded environment vars
declare -A ENVIRONMENT_VARS
ENVIRONMENT_VARS[APPLICATION_KEY]="K0000L+ZHdPrf3wT4G+7enptKGSct68"
ENVIRONMENT_VARS[APPLICATION_KEY_ID]="0003976a482cd540000000001"
ENVIRONMENT_VARS[BUCKET_NAME]="file-rep0"
ENVIRONMENT_VARS[DATABASE_URL]="postgres://viiifcyupwxvin:d8262ffd64dca62a110b013fa939c6a08a553f08aee223d315fa8428d58a88b8@ec2-54-247-177-254.eu-west-1.compute.amazonaws.com:5432/dfqgciolfgj7gg"
ENVIRONMENT_VARS[SENDGRID_API_KEY]="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"
ENVIRONMENT_VARS[SENDGRID_PASSWORD]="kzaidkww3818"
ENVIRONMENT_VARS[SENDGRID_USERNAME]="app159507625@heroku.com"

if [ ! -f "Procfile" ]; then
    echo "Procfile doesn't exist in the current directory. Are you sure this is a forkie dir"
    exit 1
fi

echo "Exporting environment variables"
for i in "${!ENVIRONMENT_VARS[@]}"; do export "$i=${ENVIRONMENT_VARS[$i]}"; done

# set -x
heroku local web

exit 1