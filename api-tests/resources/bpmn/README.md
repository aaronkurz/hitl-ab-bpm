# Test BPMN Process Models

These process models have been created for testing and experimentation purposes.
They can be deployed to the Camunda engine, like any BPMN file. But additionally, they have been annotated with extension properties, which allow for the automatic simulation.
When deployed to a Camunda engine with the [Camunda BPM simulator plugin](https://github.com/camunda-consulting/camunda-bpm-simulator) installed, any instances of a process with such extension properties are simulated.
Below, you can find an outline on the test processes we created and what behavior you can expect from them.

## Simulation Properties

| Name            | Description                                                                                                                                     | Avg. Duration A s | Avg. Duration B s | Ran simulation for data json with break of how many s in between instances |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-------------------|----------------------------------------------------------------------------|
| helicopter      | Essentially the same as the process used as an example in a publication by Suhrid Satyal\*, but with a different timeframe: 1 day -> one second | 64.2              | 21                | 5                                                                          |
| fast\_a\_better | A should only take about half the time of B                                                                                                     | 1.1               | 2.1               | 1                                                                          |

\* [Business process improvement with the AB-BPM methodology, p. 18](https://www.diciccio.net/claudio/preprints/Satyal-etal-IS2019-BusinessProcessImprovementwithABBPM.pdf)
