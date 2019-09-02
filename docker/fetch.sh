# initially kill running processes
pkill -f Fetch

# start fetch script
LOGS=/home/opwu/portalwatch_data/logs
LOGF=Fetch_$week
SCRIPT="docker run -v /home/opwu/portalwatch_data/virtuoso/dumps/data:/data --rm --network=\"host\" odpw -v Fetch"
cmd="$SCRIPT 1>> $LOGS/$LOGF.out 2> $LOGS/$LOGF.err"
echo $cmd
eval $cmd