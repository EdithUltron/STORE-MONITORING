import React, { useState } from "react";
import axios from "axios";
import {
  Button,
  Container,
  Row,
  Col,
  Alert,
  Spinner,
  Table,
} from "react-bootstrap";
import { FileEarmarkArrowDown } from "react-bootstrap-icons";

const API_BASE_URL = "http://localhost:8000";

function App() {
  const [loading, setLoading] = useState(false);
  const [reportId, setReportId] = useState("");
  const [showAlert, setShowAlert] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportData, setReportData] = useState(null);

  const handleTriggerReport = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/trigger_report`);
      const { report_id: newReportId } = response.data;
      setReportId(newReportId);
      setShowAlert(true);
    } catch (error) {
      console.error("Error triggering report:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportData = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/get_report?report_id=${reportId}`
      );
      const { status, data } = response.data;
      if (status === "Running") {
        // If the report is still running, wait for a short delay and fetch again
        await new Promise((resolve) => setTimeout(resolve, 1000));
        fetchReportData();
      } else if (status === "Complete") {
        console.log("Report Data:", data);
        setReportData(data);
        setLoadingReport(false);
      }
    } catch (error) {
      console.error("Error getting report:", error);
      setLoadingReport(false);
    }
  };

  const handleGetReport = async () => {
    try {
      setLoadingReport(true);
      await fetchReportData();
    } catch (error) {
      console.error("Error fetching report:", error);
      setLoadingReport(false);
    }
  };

  const handleDownloadCSV = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/download_report?report_id=${reportId}`,
        {
          responseType: "blob", // Set the response type to blob to handle binary data
        }
      );

      // Create a URL for the blob data and create a temporary link to download the file
      const blobUrl = URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", "report.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up the blob URL after the download is complete
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Error downloading CSV:", error);
    }
  };

  return (
    <Container>
      <Row className='my-4'>
        <Col>
          <Button
            variant='primary'
            onClick={handleTriggerReport}
            disabled={loading}>
            {loading ? <Spinner animation='border' /> : "Trigger Report"}
          </Button>
          {showAlert && (
            <Alert
              variant='success'
              className='mt-3'
              onClose={() => setShowAlert(false)}
              dismissible>
              Report triggered successfully! Report ID: {reportId}
            </Alert>
          )}
        </Col>
      </Row>
      <Row className='my-4'>
        <Col>
          <Button
            variant='info'
            onClick={handleGetReport}
            disabled={!reportId || loading || loadingReport}>
            {loadingReport ? <Spinner animation='border' /> : "View Report"}
          </Button>
        </Col>
      </Row>
      {reportData && (
        <Row>
          <Col>
            <h3>Report Data:</h3>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Store ID</th>
                  <th>Uptime (Last Hour)</th>
                  <th>Uptime (Last Day)</th>
                  <th>Uptime (Last Week)</th>
                  <th>Downtime (Last Hour)</th>
                  <th>Downtime (Last Day)</th>
                  <th>Downtime (Last Week)</th>
                </tr>
              </thead>
              <tbody>
                {reportData.map((item) => (
                  <tr key={item.store_id}>
                    <td>{item.store_id}</td>
                    <td>{item.uptime_last_hour} minutes</td>
                    <td>{item.uptime_last_day} hours</td>
                    <td>{item.uptime_last_week} hours</td>
                    <td>{item.downtime_last_hour} minutes</td>
                    <td>{item.downtime_last_day} hours</td>
                    <td>{item.downtime_last_week} hours</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Col>
        </Row>
      )}
      {reportData && (
        <Row className='my-4'>
          <Col>
            <Button variant='success' onClick={handleDownloadCSV}>
              <FileEarmarkArrowDown className='mr-2' /> Download CSV
            </Button>
          </Col>
        </Row>
      )}
    </Container>
  );
}

export default App;
