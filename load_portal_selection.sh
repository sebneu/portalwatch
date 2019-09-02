for file in portal_selection/*.csv
do
	echo $file
	pid=${file#portal_selection/}
	pid=${pid%_snapshots.csv}
	echo $pid
	docker run -v ~/portalwatch_data/virtuoso/dumps/data:/data --rm --network="host" odpw -v DBExport --host datamonitor-data.ai.wu.ac.at --port 5432 --user opwu --password 0pwu --db portalwatch --portal $pid --file $file
done
