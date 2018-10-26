package se.nbis.lega.cucumber.pojo;

import java.util.Arrays;

public enum FileStatus {

    RECEIVED("READY"),
    IN_PROGRESS("IN_INGESTION"),
    COMPLETED("COMPLETED"),
    ARCHIVED("ARCHIVED"),
    ERROR("ERROR"),
    UNDEFINED("(0 rows)");


    private final String status;

    FileStatus(String status) {
        this.status = status;
    }

    public String getStatus() {
        return status;
    }

    public static FileStatus getValue(String status) {
        return Arrays.stream(FileStatus.values()).filter(fs -> fs.status.equals(status)).findAny().orElse(FileStatus.UNDEFINED);
    }

}
