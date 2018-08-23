package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

@Slf4j
public class Robustness implements En {

    public Robustness(Context context) {
        Utils utils = context.getUtils();

        When("^the system is restarted$", utils::restartAllLocalEGAContainers);
    }

}
