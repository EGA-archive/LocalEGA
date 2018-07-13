package se.nbis.lega.cucumber.pojo;

public enum FileStatus {

    RECEIVED("Received"),
    IN_PROGRESS("In progress"),
    COMPLETED("Completed"),
    ARCHIVED("Archived"),
    ERROR("Error");

    private final String status;

    FileStatus(String status) {
        this.status = status;
    }

    public String getStatus() {
        return status;
    }

}
